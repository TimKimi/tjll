"""LangGraph ask 对外服务：流式生成、历史、洞察与 interrupt 占位接口。"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

from backend.config import settings
from backend.llm.client.llm import get_llm
from backend.llm.graph.builder import get_ask_session, release_ask_session
from backend.llm.graph.nodes import history_snapshot
from backend.llm.graph.session_pool import get_session_pool
from backend.llm.insight.registry import ensure_section_insight, ensure_user_insight
from backend.llm.prompts.rag import RAG_PROMPT_WITH_HISTORY
from backend.llm.schemas import (
    AskInterruptCreateRequest,
    AskInterruptCreateResponse,
    AskInterruptSubmitRequest,
    AskInterruptSubmitResponse,
    AskRequest,
    AskResponse,
    DeleteHistoryByUuidRequest,
    DeleteHistoryResponse,
    DeleteInsightResponse,
    HistoryMessage,
    HistoryRequest,
    HistoryResponse,
    LoadSectionDocumentRequest,
    LoadSectionDocumentResponse,
    RagSnippet,
    ReleaseSessionsResponse,
    SectionFactsResponse,
    SectionInsightResponse,
    SectionReviewResponse,
    SetSectionReviewRequest,
    UpdateSectionFactsRequest,
    UpdateSectionInsightAttrsRequest,
    UpdateUserInsightAttrsRequest,
    UserInsightResponse,
    UuidRequest,
)
from backend.llm.session.history import clear_histories_for_uuid, clear_history
from backend.logging_setup import setup_app_logging

logger = logging.getLogger("backend.llm.graph.service")

_ATTACHMENT_FIELDS = ("docx", "doc", "txt", "md", "pdf", "images")


def _iter_ask_attachment_paths(request: AskRequest) -> list[str]:
    """从 AskRequest 六个附件字段收集非空路径。"""
    paths: list[str] = []
    for name in _ATTACHMENT_FIELDS:
        value = getattr(request, name, None)
        if value is None:
            continue
        if isinstance(value, str):
            text = value.strip()
            if text:
                paths.append(text)
            continue
        if isinstance(value, (list, tuple)):
            for item in value:
                if item is None:
                    continue
                text = str(item).strip()
                if text:
                    paths.append(text)
            continue
        text = str(value).strip()
        if text:
            paths.append(text)
    return paths


def _mark_ask_used_filenames(request: AskRequest, section) -> list[str]:
    """带文件的 ask：只更新 used_filenames；加载由 load_section_document 完成。

    返回本轮请求体原始非空路径（供 query_filename）。
    """
    paths = _iter_ask_attachment_paths(request)
    if not paths:
        return []
    section.add_used_filenames(paths)
    return paths


class AskStream:
    """流式 ask：``for x in stream`` 得到 answer 文本块；耗尽后读 ``response``。"""

    def __init__(self, chunks: Iterator[str], holder: dict[str, AskResponse | None]):
        self._chunks = chunks
        self._holder = holder

    def __iter__(self) -> Iterator[str]:
        yield from self._chunks

    @property
    def response(self) -> AskResponse | None:
        return self._holder.get("response")


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
        role = h.get("role") or "system"
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
        out.append(
            HistoryMessage(
                role=role,  # type: ignore[arg-type]
                content=str(h.get("content") or ""),
                filename=(h.get("filename") or "") if role == "user" else None,
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


def _parse_uuid(
    req: UuidRequest | DeleteHistoryByUuidRequest | dict[str, Any] | str | None,
    *,
    uuid: str | None,
) -> str:
    if isinstance(req, str):
        uuid = req
    elif req is not None:
        if isinstance(req, (UuidRequest, DeleteHistoryByUuidRequest)):
            uuid = req.uuid
        else:
            uuid = UuidRequest.model_validate(req).uuid
    text = (uuid or "").strip()
    if not text:
        raise ValueError("uuid is required")
    return text


def _parse_history_ids(
    req: HistoryRequest | dict[str, Any] | None,
    *,
    uuid: str | None,
    section_id: str | None,
) -> tuple[str, str]:
    if req is not None:
        request = (
            req
            if isinstance(req, HistoryRequest)
            else HistoryRequest.model_validate(req)
        )
        uuid = request.uuid
        section_id = request.section_id
    u = (uuid or "").strip()
    s = (section_id or "").strip()
    if not u or not s:
        raise ValueError("uuid and section_id are both required")
    return u, s


def get_ask_history(
    req: HistoryRequest | dict[str, Any] | None = None,
    *,
    uuid: str | None = None,
    section_id: str | None = None,
) -> HistoryResponse:
    """按 uuid + section_id 返回完整会话历史（含扩展字段）。"""
    setup_app_logging()
    uuid, section_id = _parse_history_ids(req, uuid=uuid, section_id=section_id)
    messages = get_session_pool().peek_history_messages(uuid, section_id)
    history = _history_to_messages(history_snapshot(messages))
    insight_create, insight_use = _last_user_insight_flags(history)
    logger.info(
        "get_ask_history uuid=%s section_id=%s messages=%d",
        uuid,
        section_id,
        len(history),
    )
    return HistoryResponse(
        uuid=uuid,
        section_id=section_id,
        history=history,
        insight_create=insight_create,
        insight_use=insight_use,
    )


def delete_ask_history(
    req: HistoryRequest | dict[str, Any] | None = None,
    *,
    uuid: str | None = None,
    section_id: str | None = None,
) -> DeleteHistoryResponse:
    """按 uuid + section_id 删除单个会话历史（内存池 + Redis）。"""
    setup_app_logging()
    uuid, section_id = _parse_history_ids(req, uuid=uuid, section_id=section_id)
    pool = get_session_pool()
    pool.discard_session(uuid, section_id)
    clear_history(uuid, section_id)
    logger.info("delete_ask_history uuid=%s section_id=%s", uuid, section_id)
    return DeleteHistoryResponse(
        uuid=uuid,
        section_id=section_id,
        deleted_sessions=1,
        section_ids=[section_id],
    )


def delete_ask_histories_by_uuid(
    req: DeleteHistoryByUuidRequest | dict[str, Any] | str | None = None,
    *,
    uuid: str | None = None,
) -> DeleteHistoryResponse:
    """按 uuid 删除该用户全部会话历史（内存池 + Redis）。"""
    setup_app_logging()
    uuid = _parse_uuid(req, uuid=uuid)
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
    return DeleteHistoryResponse(
        uuid=uuid,
        section_id=None,
        deleted_sessions=len(section_ids),
        section_ids=section_ids,
    )


def release_ask_sessions_by_uuid(
    req: UuidRequest | dict[str, Any] | str | None = None,
    *,
    uuid: str | None = None,
) -> ReleaseSessionsResponse:
    """按 uuid 释放该用户在内存会话池中的全部槽位（刷 Redis，不删历史）。"""
    setup_app_logging()
    uuid = _parse_uuid(req, uuid=uuid)
    discarded = get_session_pool().release_sessions_for_uuid(uuid)
    section_ids = sorted(k.split("::", 1)[1] for k in discarded if "::" in k)
    logger.info(
        "release_ask_sessions_by_uuid uuid=%s released=%d",
        uuid,
        len(section_ids),
    )
    return ReleaseSessionsResponse(
        uuid=uuid,
        released_sessions=len(section_ids),
        section_ids=section_ids,
    )


def on_user_logout(
    req: UuidRequest | dict[str, Any] | str | None = None,
    *,
    uuid: str | None = None,
) -> ReleaseSessionsResponse:
    """用户退出登录钩子：清除该 uuid 在会话池中的全部槽位。

    当前与 ``release_ask_sessions_by_uuid`` 同契约；后续可扩展其它登出清理。
    """
    return release_ask_sessions_by_uuid(req, uuid=uuid)


def delete_user_insight(
    req: UuidRequest | dict[str, Any] | str | None = None,
    *,
    uuid: str | None = None,
) -> DeleteInsightResponse:
    """删除用户总体洞察（占位）。"""
    setup_app_logging()
    uuid = _parse_uuid(req, uuid=uuid)
    logger.info("delete_user_insight placeholder uuid=%s", uuid)
    return DeleteInsightResponse(uuid=uuid, section_id=None, deleted=True, scope="user")


def delete_section_insight(
    req: HistoryRequest | dict[str, Any] | None = None,
    *,
    uuid: str | None = None,
    section_id: str | None = None,
) -> DeleteInsightResponse:
    """删除单个会话洞察（占位）。"""
    setup_app_logging()
    uuid, section_id = _parse_history_ids(req, uuid=uuid, section_id=section_id)
    logger.info(
        "delete_section_insight placeholder uuid=%s section_id=%s",
        uuid,
        section_id,
    )
    return DeleteInsightResponse(
        uuid=uuid, section_id=section_id, deleted=True, scope="section"
    )


def delete_all_insights(
    req: UuidRequest | dict[str, Any] | str | None = None,
    *,
    uuid: str | None = None,
) -> DeleteInsightResponse:
    """删除该用户全部洞察（含各会话）（占位）。"""
    setup_app_logging()
    uuid = _parse_uuid(req, uuid=uuid)
    logger.info("delete_all_insights placeholder uuid=%s", uuid)
    return DeleteInsightResponse(uuid=uuid, section_id=None, deleted=True, scope="all")


def get_user_insight(
    req: UuidRequest | dict[str, Any] | str | None = None,
    *,
    uuid: str | None = None,
) -> UserInsightResponse:
    """查询用户总体洞察属性字典（占位返回空 attrs）。"""
    setup_app_logging()
    uuid = _parse_uuid(req, uuid=uuid)
    return UserInsightResponse(uuid=uuid, attrs={})


def get_section_insight(
    req: HistoryRequest | dict[str, Any] | None = None,
    *,
    uuid: str | None = None,
    section_id: str | None = None,
) -> SectionInsightResponse:
    """查询会话洞察属性（占位：空 attrs / filenames；日后可动态合并父类属性）。"""
    setup_app_logging()
    uuid, section_id = _parse_history_ids(req, uuid=uuid, section_id=section_id)
    return SectionInsightResponse(
        uuid=uuid, section_id=section_id, attrs={}, filenames=[]
    )


def update_user_insight_attrs(
    req: UpdateUserInsightAttrsRequest | dict[str, Any],
) -> UserInsightResponse:
    """批量更新用户总体洞察属性（占位：原样回传 attrs 字符串化视图）。"""
    setup_app_logging()
    request = (
        req
        if isinstance(req, UpdateUserInsightAttrsRequest)
        else UpdateUserInsightAttrsRequest.model_validate(req)
    )
    attrs = {str(k): str(v) for k, v in (request.attrs or {}).items() if v is not None}
    logger.info(
        "update_user_insight_attrs placeholder uuid=%s keys=%d",
        request.uuid,
        len(attrs),
    )
    return UserInsightResponse(uuid=request.uuid, attrs=attrs)


def update_section_insight_attrs(
    req: UpdateSectionInsightAttrsRequest | dict[str, Any],
) -> SectionInsightResponse:
    """批量更新会话洞察属性（占位）。"""
    setup_app_logging()
    request = (
        req
        if isinstance(req, UpdateSectionInsightAttrsRequest)
        else UpdateSectionInsightAttrsRequest.model_validate(req)
    )
    attrs = {str(k): str(v) for k, v in (request.attrs or {}).items() if v is not None}
    logger.info(
        "update_section_insight_attrs placeholder uuid=%s section_id=%s keys=%d",
        request.uuid,
        request.section_id,
        len(attrs),
    )
    return SectionInsightResponse(
        uuid=request.uuid,
        section_id=request.section_id,
        attrs=attrs,
        filenames=[],
    )


def get_section_facts(
    req: HistoryRequest | dict[str, Any] | None = None,
    *,
    uuid: str | None = None,
    section_id: str | None = None,
) -> SectionFactsResponse:
    """读取会话 facts（占位空列表）。"""
    setup_app_logging()
    uuid, section_id = _parse_history_ids(req, uuid=uuid, section_id=section_id)
    return SectionFactsResponse(uuid=uuid, section_id=section_id, facts=[])


def update_section_facts(
    req: UpdateSectionFactsRequest | dict[str, Any],
) -> SectionFactsResponse:
    """写入会话 facts（占位：回传 items）。"""
    setup_app_logging()
    request = (
        req
        if isinstance(req, UpdateSectionFactsRequest)
        else UpdateSectionFactsRequest.model_validate(req)
    )
    items = [str(x) for x in (request.items or [])]
    logger.info(
        "update_section_facts placeholder uuid=%s section_id=%s start=%s n=%d",
        request.uuid,
        request.section_id,
        request.start,
        len(items),
    )
    return SectionFactsResponse(
        uuid=request.uuid, section_id=request.section_id, facts=items
    )


def get_section_review(
    req: HistoryRequest | dict[str, Any] | None = None,
    *,
    uuid: str | None = None,
    section_id: str | None = None,
) -> SectionReviewResponse:
    """读取会话 review（占位空串）。"""
    setup_app_logging()
    uuid, section_id = _parse_history_ids(req, uuid=uuid, section_id=section_id)
    return SectionReviewResponse(uuid=uuid, section_id=section_id, review="")


def set_section_review(
    req: SetSectionReviewRequest | dict[str, Any],
) -> SectionReviewResponse:
    """覆盖写入会话 review（占位：回传 text）。"""
    setup_app_logging()
    request = (
        req
        if isinstance(req, SetSectionReviewRequest)
        else SetSectionReviewRequest.model_validate(req)
    )
    text = "" if request.text is None else str(request.text)
    logger.info(
        "set_section_review placeholder uuid=%s section_id=%s len=%d",
        request.uuid,
        request.section_id,
        len(text),
    )
    return SectionReviewResponse(
        uuid=request.uuid, section_id=request.section_id, review=text
    )


def load_section_document(
    req: LoadSectionDocumentRequest | dict[str, Any],
) -> LoadSectionDocumentResponse:
    """加载会话文档：ensure 洞察 → load_file → 成功则删磁盘原文件。"""
    setup_app_logging()
    request = (
        req
        if isinstance(req, LoadSectionDocumentRequest)
        else LoadSectionDocumentRequest.model_validate(req)
    )
    path = (request.file_path or "").strip()
    if not path:
        raise ValueError("file_path is required")
    ensure_user_insight(request.uuid)
    section = ensure_section_insight(request.uuid, request.section_id)
    result = section.load_file(path)
    source_file = str(result.get("source_file") or path)
    chunks = int(result.get("chunks") or 0)
    errors = result.get("errors") or []
    if not errors:
        try:
            from backend.rag.document.paths import resolve_repo_path

            disk = resolve_repo_path(path)
            if disk.is_file():
                disk.unlink()
                logger.info("load_section_document deleted source path=%s", disk)
        except Exception:
            logger.exception(
                "load_section_document delete source failed path=%s",
                path,
            )
    else:
        logger.warning(
            "load_section_document errors uuid=%s section_id=%s path=%s errors=%s",
            request.uuid,
            request.section_id,
            source_file,
            errors,
        )
    logger.info(
        "load_section_document ok uuid=%s section_id=%s file=%s chunks=%d",
        request.uuid,
        request.section_id,
        source_file,
        chunks,
    )
    return LoadSectionDocumentResponse(
        uuid=request.uuid,
        section_id=request.section_id,
        source_file=source_file,
        chunks=chunks,
        filenames=section.filenames(),
    )


def create_ask_interrupt(
    req: AskInterruptCreateRequest | dict[str, Any],
) -> AskInterruptCreateResponse:
    """创建澄清问卷（占位：空 questions / 空 interrupt_id）。"""
    setup_app_logging()
    request = (
        req
        if isinstance(req, AskInterruptCreateRequest)
        else AskInterruptCreateRequest.model_validate(req)
    )
    logger.info(
        "create_ask_interrupt placeholder uuid=%s section_id=%s",
        request.uuid,
        request.section_id,
    )
    return AskInterruptCreateResponse(
        uuid=request.uuid,
        section_id=request.section_id,
        interrupt_id="",
        questions=[],
    )


def submit_ask_interrupt(
    req: AskInterruptSubmitRequest | dict[str, Any],
) -> AskInterruptSubmitResponse:
    """提交澄清答案（占位：accepted=False）。"""
    setup_app_logging()
    request = (
        req
        if isinstance(req, AskInterruptSubmitRequest)
        else AskInterruptSubmitRequest.model_validate(req)
    )
    logger.info(
        "submit_ask_interrupt placeholder uuid=%s section_id=%s interrupt_id=%s n=%d",
        request.uuid,
        request.section_id,
        request.interrupt_id,
        len(request.answers or []),
    )
    return AskInterruptSubmitResponse(
        uuid=request.uuid,
        section_id=request.section_id,
        interrupt_id=request.interrupt_id,
        accepted=False,
    )


def ask(req: AskRequest | dict[str, Any]) -> AskStream:
    """流式 ask：图完成重述/检索后，流式生成 answer。

    - ``sources`` 由 retrieve 工具写入会话侧车，不进 State
    - 本轮 history 写入内存；会话释放 / 空闲超时 / LRU 时刷 Redis
    - 会话历史请用 ``get_ask_history``；本响应不含 history
    - 附件字段只 ``add_used_filenames``；文件加载请用 ``load_section_document``
    """
    request = req if isinstance(req, AskRequest) else AskRequest.model_validate(req)
    logger.info(
        "graph ask start section_id=%s uuid=%s query_len=%d "
        "insight_create=%s insight_use=%s",
        request.section_id,
        request.uuid,
        len(request.query),
        request.insight_create,
        request.insight_use,
    )

    ensure_user_insight(request.uuid)
    section = ensure_section_insight(request.uuid, request.section_id)
    session = get_ask_session(request.uuid, request.section_id)
    session.section_insight = section

    used_paths = _mark_ask_used_filenames(request, section)
    query_filename = ",".join(used_paths)

    history_before = list(session.history)
    graph = session.graph
    if graph is None:
        raise RuntimeError("ask session has no compiled graph")

    final = graph.invoke(
        {
            "query": request.query,
            "section_id": request.section_id,
            "uuid": request.uuid,
            "insight_create": request.insight_create,
            "insight_use": request.insight_use,
            "history": history_before,
        },
        config={
            "configurable": {
                "thread_id": f"{request.uuid}::{request.section_id}",
            }
        },
    )
    context = str(final.get("context") or "")
    search_query = str(
        final.get("search_query") or session.last_search_query or request.query
    )
    holder: dict[str, AskResponse | None] = {"response": None}

    def _chunks() -> Iterator[str]:
        llm = get_llm(temperature=settings.llm_generate_temperature)
        messages = RAG_PROMPT_WITH_HISTORY.format_messages(
            context=context,
            query=request.query,
            history=list(history_before),
        )
        parts: list[str] = []
        try:
            for chunk in llm.stream(messages):
                text = getattr(chunk, "content", None)
                if text is None:
                    continue
                piece = text if isinstance(text, str) else str(text)
                if not piece:
                    continue
                parts.append(piece)
                yield piece
        except Exception:
            logger.exception(
                "graph ask stream failed section_id=%s uuid=%s",
                request.section_id,
                request.uuid,
            )
            raise

        answer = "".join(parts)
        sources = list(session.last_sources)
        session.append_turn(
            request.query,
            answer,
            search_query=search_query,
            filename=query_filename,
            insight_create=request.insight_create,
            insight_use=request.insight_use,
            sources=sources,
            used=False,
        )
        resp = AskResponse(
            query=request.query,
            section_id=request.section_id,
            uuid=request.uuid,
            answer=answer,
            sources=_sources_to_snippets(sources),
            query_filename=query_filename,
        )
        holder["response"] = resp
        logger.info(
            "graph ask ok section_id=%s sources=%d answer_len=%d search_query=%r",
            request.section_id,
            len(resp.sources),
            len(answer),
            search_query,
        )

    return AskStream(_chunks(), holder)


__all__ = [
    "AskStream",
    "ask",
    "create_ask_interrupt",
    "delete_all_insights",
    "delete_ask_histories_by_uuid",
    "delete_ask_history",
    "delete_section_insight",
    "delete_user_insight",
    "get_ask_history",
    "get_section_facts",
    "get_section_insight",
    "get_section_review",
    "get_user_insight",
    "load_section_document",
    "on_user_logout",
    "release_ask_session",
    "release_ask_sessions_by_uuid",
    "set_section_review",
    "submit_ask_interrupt",
    "update_section_facts",
    "update_section_insight_attrs",
    "update_user_insight_attrs",
]
