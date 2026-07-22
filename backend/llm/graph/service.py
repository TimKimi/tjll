"""LangGraph ask 对外服务：流式生成与历史查询。"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

from backend.config import settings
from backend.llm.client.llm import get_llm
from backend.llm.graph.builder import get_ask_session, release_ask_session
from backend.llm.graph.nodes import history_snapshot
from backend.llm.graph.session_pool import get_session_pool
from backend.llm.prompts.rag import RAG_PROMPT_WITH_HISTORY
from backend.llm.schemas import (
    AskRequest,
    AskResponse,
    DeleteHistoryByUuidRequest,
    DeleteHistoryResponse,
    HistoryMessage,
    HistoryRequest,
    HistoryResponse,
    RagSnippet,
)
from backend.llm.session.history import clear_histories_for_uuid, clear_history
from backend.logging_setup import setup_app_logging

logger = logging.getLogger("backend.llm.graph.service")


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
    """组对外历史：filename / insight_create / sources；不含 search_query。"""
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
        out.append(
            HistoryMessage(
                role=role,  # type: ignore[arg-type]
                content=str(h.get("content") or ""),
                filename=(h.get("filename") or "") if role == "user" else None,
                insight_create=insight_create,
                sources=sources,
            )
        )
    return out


def get_ask_history(
    req: HistoryRequest | dict[str, Any] | None = None,
    *,
    uuid: str | None = None,
    section_id: str | None = None,
) -> HistoryResponse:
    """按 uuid + section_id 返回完整会话历史（含扩展字段）。"""
    setup_app_logging()
    if req is not None:
        request = (
            req
            if isinstance(req, HistoryRequest)
            else HistoryRequest.model_validate(req)
        )
        uuid = request.uuid
        section_id = request.section_id
    if not uuid or not section_id:
        raise ValueError("uuid and section_id are both required")
    messages = get_session_pool().peek_history_messages(uuid, section_id)
    history = _history_to_messages(history_snapshot(messages))
    logger.info(
        "get_ask_history uuid=%s section_id=%s messages=%d",
        uuid,
        section_id,
        len(history),
    )
    return HistoryResponse(uuid=uuid, section_id=section_id, history=history)


def delete_ask_history(
    req: HistoryRequest | dict[str, Any] | None = None,
    *,
    uuid: str | None = None,
    section_id: str | None = None,
) -> DeleteHistoryResponse:
    """按 uuid + section_id 删除单个会话历史（内存池 + Redis）。"""
    setup_app_logging()
    if req is not None:
        request = (
            req
            if isinstance(req, HistoryRequest)
            else HistoryRequest.model_validate(req)
        )
        uuid = request.uuid
        section_id = request.section_id
    if not uuid or not section_id:
        raise ValueError("uuid and section_id are both required")
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
    if isinstance(req, str):
        uuid = req
    elif req is not None:
        request = (
            req
            if isinstance(req, DeleteHistoryByUuidRequest)
            else DeleteHistoryByUuidRequest.model_validate(req)
        )
        uuid = request.uuid
    if not uuid:
        raise ValueError("uuid is required")
    pool = get_session_pool()
    discarded = pool.discard_sessions_for_uuid(uuid)
    cleared = clear_histories_for_uuid(uuid)
    # 合并池内已丢弃但 Redis 可能尚无 key 的 section
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


def ask(req: AskRequest | dict[str, Any]) -> AskStream:
    """流式 ask：图完成重述/检索后，流式生成 answer。

    - ``sources`` 由 retrieve 工具写入会话侧车，不进 State
    - 本轮 history 写入内存后立即刷 Redis（``uuid::section_id``）
    - 会话历史请用 ``get_ask_history``；本响应不含 history
    - ``query_filename`` 表示本轮附件文件名，暂固定为空串
    """
    setup_app_logging()
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

    session = get_ask_session(request.uuid, request.section_id)
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
    # 本轮请求附带文件名：暂空，后续维护
    query_filename = ""
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
            sources=sources,
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
    "ask",
    "AskStream",
    "delete_ask_histories_by_uuid",
    "delete_ask_history",
    "get_ask_history",
    "release_ask_session",
]
