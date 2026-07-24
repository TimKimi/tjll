"""LangGraph ask 对外服务：流式生成、历史、洞察与 rewrite HITL。"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

from backend.config import settings
from backend.llm.client.llm import _message_text, get_llm
from backend.llm.client.tool_loop import run_tool_loop
from backend.llm.graph.builder import get_ask_session, release_ask_session
from backend.llm.graph.history_window import filter_chat_messages
from backend.llm.graph.interrupt import AskInterruptSignal
from backend.llm.graph.nodes import history_snapshot, retrieve_rerank, rewrite
from backend.llm.graph.session_pool import get_session_pool, wait_section_ready
from backend.llm.insight.registry import (
    ensure_section_insight,
    ensure_user_insight,
    get_insight_registry,
)
from backend.llm.prompts.rag import RAG_PROMPT_WITH_HISTORY
from backend.llm.schemas import (
    AskHistory,
    AskInterruptQuestion,
    AskInterruptResult,
    AskInterruptSubmitParams,
    AskParams,
    AskResult,
    DeleteHistoryResult,
    HistoryMessage,
    RagSnippet,
)
from backend.llm.session.history import (
    clear_histories_for_uuid,
    clear_history,
    list_history_session_ids_for_uuid,
)
from backend.logging_setup import setup_app_logging
from backend.rag.document.indexing import (
    delete_insight_from_opensearch,
    delete_section_insight_from_opensearch,
)
from backend.rag.document.paths import normalize_backend_path, resolve_repo_path

logger = logging.getLogger("backend.llm.graph.service")

_ATTACHMENT_FIELDS = ("docx", "doc", "txt", "md", "pdf", "images")


def _require_uuid(uuid: str) -> str:
    text = (uuid or "").strip()
    if not text:
        raise ValueError("uuid is required")
    return text


def _require_ids(uuid: str, section_id: str) -> tuple[str, str]:
    u = (uuid or "").strip()
    s = (section_id or "").strip()
    if not u or not s:
        raise ValueError("uuid and section_id are both required")
    return u, s


def _normalize_attachment_value(value: Any) -> Any:
    """将附件字段中的路径规范为 ./backend/...；非法则丢弃。"""
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        return normalize_backend_path(text)
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if not text:
                continue
            norm = normalize_backend_path(text)
            if norm:
                out.append(norm)
        return out or None
    text = str(value).strip()
    if not text:
        return None
    return normalize_backend_path(text)


def _normalize_ask_params_paths(params: AskParams) -> AskParams:
    """规范化 AskParams 附件路径（就地更新副本字段）。"""
    data = params.model_dump()
    changed = False
    for name in _ATTACHMENT_FIELDS:
        raw = data.get(name)
        norm = _normalize_attachment_value(raw)
        if norm != raw:
            data[name] = norm
            changed = True
    return AskParams.model_validate(data) if changed else params


def _iter_ask_attachment_paths(params: AskParams) -> list[str]:
    """从 AskParams 六个附件字段收集规范化后的非空路径。"""
    paths: list[str] = []
    for name in _ATTACHMENT_FIELDS:
        value = getattr(params, name, None)
        if value is None:
            continue
        raw_items: list[Any]
        if isinstance(value, str):
            raw_items = [value]
        elif isinstance(value, (list, tuple)):
            raw_items = list(value)
        else:
            raw_items = [value]
        for item in raw_items:
            if item is None:
                continue
            text = str(item).strip()
            if not text:
                continue
            norm = normalize_backend_path(text)
            if not norm:
                logger.warning("skip invalid attachment path=%r", text)
                continue
            if norm not in paths:
                paths.append(norm)
    return paths


def _mark_ask_used_filenames(params: AskParams, section) -> list[str]:
    """带文件的 ask：只更新 used_filenames；加载由 load_section_document 完成。

    返回本轮规范化路径（供 query_filename）。
    """
    paths = _iter_ask_attachment_paths(params)
    if not paths:
        return []
    section.add_used_filenames(paths)
    return paths


class AskStream:
    """流式 ask：``for x in stream`` 得到 answer 文本块；耗尽后读 ``response``。"""

    def __init__(self, chunks: Iterator[str], holder: dict[str, AskResult | None]):
        self._chunks = chunks
        self._holder = holder

    def __iter__(self) -> Iterator[str]:
        yield from self._chunks

    @property
    def response(self) -> AskResult | None:
        return self._holder.get("response")


def _discard_abandoned_interrupt(session, section) -> None:
    """新 ask 开始时：若有未 submit 的挂起，视为未发生，先清空。"""
    had_pending = bool(session.pending_ask) or bool(session.pending_enrich)
    had_qa = bool(section.get_interrupt_qa())
    if not had_pending and not had_qa:
        return
    session.pending_ask = None
    session.pending_enrich = {}
    section.clear_interrupt_qa()
    logger.info(
        "discard abandoned interrupt uuid=%s section_id=%s had_pending=%s had_qa=%s",
        section.uuid,
        section.section_id,
        had_pending,
        had_qa,
    )


def _sources_to_snippets(sources: list[dict[str, Any]] | None) -> list[RagSnippet]:
    return [
        RagSnippet(
            content=str(item.get("content") or ""),
            metadata={
                k: v
                for k, v in dict(item.get("metadata") or {}).items()
                if k != "embedding"
            },
        )
        for item in (sources or [])
    ]


def _history_to_messages(snapshot: list[dict[str, Any]]) -> list[HistoryMessage]:
    """组对外历史：filename / insight_* / sources；不含 search_query / used。"""
    out: list[HistoryMessage] = []
    for h in snapshot:
        role = h.get("role") or "user"
        if role == "system":
            continue
        sources_raw = h.get("sources")
        sources = (
            _sources_to_snippets(sources_raw)
            if role == "assistant" and sources_raw is not None
            else None
        )
        insight_create = (
            bool(h.get("insight_create", False)) if role == "user" else None
        )
        insight_use = bool(h.get("insight_use", False)) if role == "user" else None
        filename = h.get("filename") or ""
        if role == "user" and filename:
            filename = normalize_backend_path(str(filename)) or str(filename)
        out.append(
            HistoryMessage(
                role=role,  # type: ignore[arg-type]
                content=str(h.get("content") or ""),
                filename=filename if role == "user" else None,
                insight_create=insight_create,
                insight_use=insight_use,
                sources=sources,
            )
        )
    return out


def _last_user_insight_flags(
    history: list[HistoryMessage],
) -> tuple[bool, bool]:
    """取末条 user 消息的 insight_create / insight_use；无则 false/false。"""
    for msg in reversed(history):
        if msg.role == "user":
            return (
                bool(msg.insight_create) if msg.insight_create is not None else False,
                bool(msg.insight_use) if msg.insight_use is not None else False,
            )
    return False, False


def get_section_ids(uuid: str) -> list[str]:
    """列出该 uuid 下全部 section_id。"""
    setup_app_logging()
    uuid = _require_uuid(uuid)
    session_ids = list_history_session_ids_for_uuid(uuid)
    section_ids = sorted(
        {
            sid.split("::", 1)[1]
            for sid in session_ids
            if "::" in sid and sid.split("::", 1)[1]
        }
    )
    logger.info("get_section_ids uuid=%s n=%d", uuid, len(section_ids))
    return section_ids


def get_ask_history(uuid: str, section_id: str) -> AskHistory:
    """按 uuid + section_id：Redis 已落盘 + AskSession 内存历史（去重拼接）。"""
    setup_app_logging()
    uuid, section_id = _require_ids(uuid, section_id)
    wait_section_ready(uuid, section_id)
    messages = filter_chat_messages(
        get_session_pool().merged_history_messages(uuid, section_id)
    )
    history = _history_to_messages(history_snapshot(messages))
    insight_create, insight_use = _last_user_insight_flags(history)
    logger.info(
        "get_ask_history uuid=%s section_id=%s messages=%d",
        uuid,
        section_id,
        len(history),
    )
    return AskHistory(
        uuid=uuid,
        section_id=section_id,
        history=history,
        insight_create=insight_create,
        insight_use=insight_use,
    )


def delete_ask_history(uuid: str, section_id: str) -> bool:
    """按 uuid + section_id 删除单个会话历史（内存池 + Redis）。"""
    setup_app_logging()
    uuid, section_id = _require_ids(uuid, section_id)
    wait_section_ready(uuid, section_id)
    pool = get_session_pool()
    pool.discard_session(uuid, section_id)
    clear_history(uuid, section_id)
    logger.info("delete_ask_history uuid=%s section_id=%s", uuid, section_id)
    return True


def delete_ask_histories_by_uuid(uuid: str) -> DeleteHistoryResult:
    """按 uuid 删除该用户全部会话历史（内存池 + Redis）。"""
    setup_app_logging()
    uuid = _require_uuid(uuid)
    pool = get_session_pool()
    discarded = pool.discard_sessions_for_uuid(uuid)
    cleared = clear_histories_for_uuid(uuid)
    section_ids = sorted(
        {
            *(sid.split("::", 1)[1] for sid in cleared if "::" in sid),
            *(k.split("::", 1)[1] for k in discarded if "::" in k),
        }
    )
    logger.info(
        "delete_ask_histories_by_uuid uuid=%s sessions=%d",
        uuid,
        len(section_ids),
    )
    return DeleteHistoryResult(
        uuid=uuid,
        section_id=None,
        deleted_sessions=len(section_ids),
        section_ids=section_ids,
    )


def release_ask_sessions_by_uuid(uuid: str) -> bool:
    """按 uuid 释放该用户在内存会话池中的全部槽位（刷 Redis，不删历史）。"""
    setup_app_logging()
    uuid = _require_uuid(uuid)
    discarded = get_session_pool().release_sessions_for_uuid(uuid)
    logger.info(
        "release_ask_sessions_by_uuid uuid=%s released=%d",
        uuid,
        len(discarded),
    )
    return True


def delete_user_insight(uuid: str) -> bool:
    """清空用户 attrs + 删 OpenSearch；Redis key 保留（attrs 为空）。"""
    setup_app_logging()
    uuid = _require_uuid(uuid)
    user = ensure_user_insight(uuid)
    user.replace_attrs({})
    user.last_chunk_size = 0
    try:
        delete_insight_from_opensearch(uuid)
    except Exception:
        logger.exception("delete_user_insight OS failed uuid=%s", uuid)
    user.save_to_redis()
    logger.info("delete_user_insight uuid=%s", uuid)
    return True


def delete_section_insight(uuid: str, section_id: str) -> bool:
    """清空会话 attrs + 删 OpenSearch 会话洞察切块；保留 facts/review。"""
    setup_app_logging()
    uuid, section_id = _require_ids(uuid, section_id)
    wait_section_ready(uuid, section_id)
    section = ensure_section_insight(uuid, section_id)
    section.replace_section_attrs({})
    section.last_section_chunk_size = 0
    try:
        delete_section_insight_from_opensearch(uuid, section_id)
    except Exception:
        logger.exception(
            "delete_section_insight OS failed uuid=%s section_id=%s",
            uuid,
            section_id,
        )
    # Redis 覆写：attrs 空，facts/review 等其它字段保留
    section.save_to_redis()
    logger.info("delete_section_insight uuid=%s section_id=%s", uuid, section_id)
    return True


def delete_all_insights(uuid: str) -> bool:
    """清空该用户全部会话/用户 attrs + 对应 OpenSearch；Redis key 保留。"""
    setup_app_logging()
    uuid = _require_uuid(uuid)
    from backend.llm.insight.store import list_section_insight_ids_for_uuid

    section_ids = set(list_section_insight_ids_for_uuid(uuid))
    reg = get_insight_registry()
    prefix = f"{uuid}::"
    with reg._lock:
        section_ids.update(
            k.split("::", 1)[1] for k in reg._sections if k.startswith(prefix)
        )
    for sid in sorted(section_ids):
        delete_section_insight(uuid, sid)
    delete_user_insight(uuid)
    logger.info("delete_all_insights uuid=%s", uuid)
    return True


def get_user_insight(uuid: str) -> dict[str, str]:
    """查询用户总体洞察属性字典。"""
    setup_app_logging()
    uuid = _require_uuid(uuid)
    return ensure_user_insight(uuid).as_dict()


def get_section_insight(uuid: str, section_id: str) -> dict[str, str]:
    """查询会话洞察属性字典（仅 section attrs）。"""
    setup_app_logging()
    uuid, section_id = _require_ids(uuid, section_id)
    wait_section_ready(uuid, section_id)
    return ensure_section_insight(uuid, section_id).section_as_dict()


def update_user_insight_attrs(uuid: str, attrs: dict[str, Any]) -> bool:
    """用完整字典覆写用户洞察属性（只改内存；释放时再覆写 Redis）。"""
    setup_app_logging()
    uuid = _require_uuid(uuid)
    user = ensure_user_insight(uuid)
    user.replace_attrs(attrs or {})
    try:
        user.split_and_store()
    except Exception:
        logger.exception("update_user_insight_attrs split failed uuid=%s", uuid)
    logger.info("update_user_insight_attrs uuid=%s keys=%d", uuid, len(attrs or {}))
    return True


def update_section_insight_attrs(
    uuid: str, section_id: str, attrs: dict[str, Any]
) -> bool:
    """用完整字典覆写会话洞察属性（只改内存；释放时再覆写 Redis）。"""
    setup_app_logging()
    uuid, section_id = _require_ids(uuid, section_id)
    wait_section_ready(uuid, section_id)
    section = ensure_section_insight(uuid, section_id)
    section.replace_section_attrs(attrs or {})
    try:
        section.split_and_store_section()
    except Exception:
        logger.exception(
            "update_section_insight_attrs split failed uuid=%s section_id=%s",
            uuid,
            section_id,
        )
    logger.info(
        "update_section_insight_attrs uuid=%s section_id=%s keys=%d",
        uuid,
        section_id,
        len(attrs or {}),
    )
    return True


def get_section_facts(uuid: str, section_id: str) -> list[str]:
    """读取会话 facts。"""
    setup_app_logging()
    uuid, section_id = _require_ids(uuid, section_id)
    wait_section_ready(uuid, section_id)
    return ensure_section_insight(uuid, section_id).get_facts()


def update_section_facts(uuid: str, section_id: str, items: list[str]) -> bool:
    """整体覆写会话 facts（只改内存；释放时再覆写 Redis）。"""
    setup_app_logging()
    uuid, section_id = _require_ids(uuid, section_id)
    wait_section_ready(uuid, section_id)
    section = ensure_section_insight(uuid, section_id)
    section.set_facts(list(items or []))
    logger.info(
        "update_section_facts uuid=%s section_id=%s n=%d",
        uuid,
        section_id,
        len(items or []),
    )
    return True


def get_section_review(uuid: str, section_id: str) -> str:
    """读取会话 review；空则回落池内首条用户 query。"""
    setup_app_logging()
    uuid, section_id = _require_ids(uuid, section_id)
    wait_section_ready(uuid, section_id)
    return ensure_section_insight(uuid, section_id).get_review_with_fallback()


def set_section_review(uuid: str, section_id: str, text: str) -> bool:
    """整体覆写会话 review（只改内存；释放时再覆写 Redis）。"""
    setup_app_logging()
    uuid, section_id = _require_ids(uuid, section_id)
    wait_section_ready(uuid, section_id)
    section = ensure_section_insight(uuid, section_id)
    section.set_review("" if text is None else str(text))
    logger.info(
        "set_section_review uuid=%s section_id=%s len=%d",
        uuid,
        section_id,
        len(section.get_review()),
    )
    return True


def load_section_document(uuid: str, section_id: str, file_path: str) -> bool:
    """加载会话文档：ensure 洞察 → load_file → 成功则删磁盘原文件。"""
    setup_app_logging()
    uuid, section_id = _require_ids(uuid, section_id)
    wait_section_ready(uuid, section_id)
    path = (file_path or "").strip()
    if not path:
        raise ValueError("file_path is required")
    norm = normalize_backend_path(path)
    if not norm:
        raise ValueError(f"file_path must be under ./backend/: {file_path}")
    ensure_user_insight(uuid)
    section = ensure_section_insight(uuid, section_id)
    result = section.load_file(norm)
    source_file = str(result.get("source_file") or norm)
    chunks = int(result.get("chunks") or 0)
    errors = result.get("errors") or []
    if not errors:
        try:
            disk = resolve_repo_path(norm)
            if disk.is_file():
                disk.unlink()
                logger.info("load_section_document deleted source path=%s", disk)
        except Exception:
            logger.exception(
                "load_section_document delete source failed path=%s",
                norm,
            )
    else:
        logger.warning(
            "load_section_document errors uuid=%s section_id=%s path=%s errors=%s",
            uuid,
            section_id,
            source_file,
            errors,
        )
        return False
    logger.info(
        "load_section_document ok uuid=%s section_id=%s file=%s chunks=%d",
        uuid,
        section_id,
        source_file,
        chunks,
    )
    return True


def _questions_from_section(section) -> list[AskInterruptQuestion]:
    out: list[AskInterruptQuestion] = []
    for item in section.get_interrupt_qa():
        if "result" in item and str(item.get("result") or "").strip():
            continue
        q = str(item.get("question") or "").strip()
        if not q:
            continue
        option = item.get("option") if isinstance(item.get("option"), dict) else {}
        out.append(
            AskInterruptQuestion(
                question=q,
                option={str(k): str(v) for k, v in dict(option or {}).items()},
            )
        )
    return out


def _make_interrupt_result(uuid: str, section_id: str, section) -> AskInterruptResult:
    return AskInterruptResult(
        uuid=uuid,
        section_id=section_id,
        questions=_questions_from_section(section),
    )


def _stream_ask_answer(
    *,
    params: AskParams,
    section,
    session,
    context: str,
    search_query: str,
    detail: str,
    query_filename: str,
    history_before: list,
) -> AskStream:
    holder: dict[str, AskResult | None] = {"response": None}

    def _chunks() -> Iterator[str]:
        messages = RAG_PROMPT_WITH_HISTORY.format_messages(
            context=context,
            query=params.query,
            history=list(history_before),
        )
        if detail.strip():
            from langchain_core.messages import HumanMessage

            messages.append(
                HumanMessage(content=f"补充细节（改写侧）：\n{detail.strip()}")
            )
        tools = [section.as_get_review_tool(), section.as_get_facts_tool()]
        parts: list[str] = []
        try:
            answered = False
            try:
                last = run_tool_loop(
                    messages,
                    tools,
                    temperature=settings.llm_generate_temperature,
                    max_rounds=4,
                )
                text = _message_text(last).strip()
                if text:
                    parts.append(text)
                    yield text
                    answered = True
            except Exception:
                logger.debug(
                    "ask tool_loop fallback to stream uuid=%s section_id=%s",
                    params.uuid,
                    params.section_id,
                    exc_info=True,
                )
            if not answered:
                llm = get_llm(temperature=settings.llm_generate_temperature)
                for chunk in llm.stream(messages):
                    piece_raw = getattr(chunk, "content", None)
                    if piece_raw is None:
                        continue
                    piece = piece_raw if isinstance(piece_raw, str) else str(piece_raw)
                    if not piece:
                        continue
                    parts.append(piece)
                    yield piece
        except Exception:
            logger.exception(
                "graph ask stream failed section_id=%s uuid=%s",
                params.section_id,
                params.uuid,
            )
            raise

        answer = "".join(parts)
        sources = list(session.last_sources)
        interrupt_qa = section.get_interrupt_qa()
        session.append_turn(
            params.query,
            answer,
            search_query=search_query,
            detail=detail,
            filename=query_filename,
            insight_create=params.insight_create,
            insight_use=params.insight_use,
            sources=sources,
            used=False,
            interrupt_qa=interrupt_qa,
        )
        section.clear_interrupt_qa()
        session.pending_ask = None
        session.pending_enrich = {}
        try:
            session.maintain()
        except Exception:
            logger.exception(
                "ask maintain failed uuid=%s section_id=%s",
                params.uuid,
                params.section_id,
            )
        result = AskResult(
            query=params.query,
            section_id=params.section_id,
            uuid=params.uuid,
            answer=answer,
            sources=_sources_to_snippets(sources),
            query_filename=query_filename,
        )
        holder["response"] = result
        logger.info(
            "graph ask ok section_id=%s sources=%d answer_len=%d search_query=%r",
            params.section_id,
            len(result.sources),
            len(answer),
            search_query,
        )

    return AskStream(_chunks(), holder)


def _resume_from_rewrite(params: AskParams, session, section) -> AskStream:
    """submit 后续跑：rewrite → retrieve → stream。"""
    from backend.llm.graph.state import AskState

    enrich = dict(session.pending_enrich or {})
    used_paths = list(enrich.get("attachment_filenames") or [])
    query_filename = ",".join(used_paths)
    history_before = list(session.history)
    state: AskState = {
        "query": params.query,
        "section_id": params.section_id,
        "uuid": params.uuid,
        "insight_use": bool(enrich.get("insight_use", params.insight_use)),
        "attachment_filenames": used_paths,
        "insight": list(enrich.get("insight") or []),
        "attachment": list(enrich.get("attachment") or []),
        "resume_rewrite": True,
    }
    out = rewrite(state)
    state["search_query"] = str(out.get("search_query") or "")
    state["detail"] = str(out.get("detail") or "")
    out2 = retrieve_rerank(state)
    state["context"] = str(out2.get("context") or "")
    if out2.get("search_query") is not None:
        state["search_query"] = str(out2.get("search_query") or "")
    context = str(state.get("context") or "")
    search_query = str(
        state.get("search_query") or session.last_search_query or params.query
    )
    detail = str(state.get("detail") or session.last_detail or "")
    return _stream_ask_answer(
        params=params,
        section=section,
        session=session,
        context=context,
        search_query=search_query,
        detail=detail,
        query_filename=query_filename,
        history_before=history_before,
    )


def submit_ask_interrupt(params: AskInterruptSubmitParams) -> AskStream:
    """写入澄清答案（option→result），从 rewrite 续跑完整 ask。"""
    setup_app_logging()
    uuid, section_id = _require_ids(params.uuid, params.section_id)
    wait_section_ready(uuid, section_id)
    section = ensure_section_insight(uuid, section_id)
    session = get_ask_session(uuid, section_id)
    session.section_insight = section

    pending_ask = session.pending_ask
    if pending_ask is None or not section.has_pending_interrupt_questions():
        raise ValueError("no pending interrupt questions for this section")

    pending_qs = {
        str(item.get("question") or "").strip()
        for item in section.get_interrupt_qa()
        if not ("result" in item and str(item.get("result") or "").strip())
        and str(item.get("question") or "").strip()
    }
    answers = list(params.answers or [])
    answer_qs = {
        str(a.question).strip()
        for a in answers
        if str(a.question).strip() and str(a.result).strip()
    }
    if pending_qs - answer_qs:
        missing = sorted(pending_qs - answer_qs)
        raise ValueError(f"missing answers for questions: {missing}")

    section.apply_interrupt_answers(
        [{"question": a.question, "result": a.result} for a in answers]
    )
    ask_params = (
        pending_ask
        if isinstance(pending_ask, AskParams)
        else AskParams.model_validate(pending_ask)
    )
    logger.info(
        "submit_ask_interrupt uuid=%s section_id=%s answers=%d",
        uuid,
        section_id,
        len(answers),
    )
    return _resume_from_rewrite(ask_params, session, section)


def ask(params: AskParams) -> AskStream | AskInterruptResult:
    """流式 ask；rewrite 若需澄清则返回 AskInterruptResult。

    - ``sources`` 由 retrieve 工具写入会话侧车，不进 State
    - 本轮 history 写入内存；会话释放 / 空闲超时 / LRU 时刷 Redis
    - 会话历史请用 ``get_ask_history``；本结果不含 history
    - 附件字段只 ``add_used_filenames``；文件加载请用 ``load_section_document``
    - 每轮末尾 ``maintain()``
    - 若有未 submit 的 interrupt 挂起，先丢弃再开新一轮
    """
    params = _normalize_ask_params_paths(params)
    wait_section_ready(params.uuid, params.section_id)
    logger.info(
        "graph ask start section_id=%s uuid=%s query_len=%d "
        "insight_create=%s insight_use=%s",
        params.section_id,
        params.uuid,
        len(params.query),
        params.insight_create,
        params.insight_use,
    )

    ensure_user_insight(params.uuid)
    section = ensure_section_insight(params.uuid, params.section_id)
    session = get_ask_session(params.uuid, params.section_id)
    session.section_insight = section  # 绑定，保证每个asksession关联一个洞察
    _discard_abandoned_interrupt(session, section)
    session.pending_ask = params  # 提前存储打断时的入参

    used_paths = _mark_ask_used_filenames(params, section)  # 存使用过的文件
    query_filename = ",".join(used_paths)  # 存state里的格式

    history_before = list(session.history)
    graph = session.graph
    if graph is None:
        raise RuntimeError("ask session has no compiled graph")

    try:
        final = graph.invoke(
            {
                "query": params.query,
                "section_id": params.section_id,
                "uuid": params.uuid,
                "insight_use": params.insight_use,
                "attachment_filenames": list(used_paths),
                "insight": [],
                "attachment": [],
            },
            config={
                "configurable": {
                    "thread_id": f"{params.uuid}::{params.section_id}",
                }
            },
        )
    except AskInterruptSignal as exc:
        logger.info(
            "ask interrupted uuid=%s section_id=%s questions=%d",
            params.uuid,
            params.section_id,
            len(exc.questions),
        )
        return _make_interrupt_result(params.uuid, params.section_id, section)

    context = str(final.get("context") or "")
    search_query = str(
        final.get("search_query") or session.last_search_query or params.query
    )
    detail = str(final.get("detail") or session.last_detail or "")
    return _stream_ask_answer(
        params=params,
        section=section,
        session=session,
        context=context,
        search_query=search_query,
        detail=detail,
        query_filename=query_filename,
        history_before=history_before,
    )


__all__ = [
    "AskStream",
    "ask",
    "delete_all_insights",
    "delete_ask_histories_by_uuid",
    "delete_ask_history",
    "delete_section_insight",
    "delete_user_insight",
    "get_ask_history",
    "get_section_facts",
    "get_section_ids",
    "get_section_insight",
    "get_section_review",
    "get_user_insight",
    "load_section_document",
    "release_ask_session",
    "release_ask_sessions_by_uuid",
    "set_section_review",
    "submit_ask_interrupt",
    "update_section_facts",
    "update_section_insight_attrs",
    "update_user_insight_attrs",
]
