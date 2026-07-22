"""LangGraph ask 对外服务：流式生成。"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

from backend.config import settings
from backend.llm.client.llm import get_llm
from backend.llm.graph.builder import get_ask_session, release_ask_session
from backend.llm.graph.nodes import history_snapshot
from backend.llm.prompts.rag import RAG_PROMPT_WITH_HISTORY
from backend.llm.schemas import (
    AskRequest,
    AskResponse,
    HistoryMessage,
    RagSnippet,
)

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
    """组响应用历史：带 filename / sources 扩展，不返回 search_query。"""
    out: list[HistoryMessage] = []
    for h in snapshot:
        role = h.get("role") or "system"
        sources_raw = h.get("sources")
        sources = (
            _sources_to_snippets(sources_raw)
            if role == "assistant" and sources_raw is not None
            else None
        )
        out.append(
            HistoryMessage(
                role=role,  # type: ignore[arg-type]
                content=str(h.get("content") or ""),
                filename=(h.get("filename") or "") if role == "user" else None,
                sources=sources,
            )
        )
    return out


def ask(req: AskRequest | dict[str, Any]) -> AskStream:
    """流式 ask：图完成重述/检索后，流式生成 answer。

    - ``sources`` 由 retrieve 工具写入会话侧车，不进 State
    - 本轮 history 写入内存后立即刷 Redis（``uuid::section_id``）
    - 响应 ``history`` 含 filename/sources 扩展，不含 search_query
    - ``query_filename`` 表示本轮附件文件名，暂固定为空串
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
        snapshot = history_snapshot(history_before)
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
            sources=sources,
        )
        resp = AskResponse(
            query=request.query,
            section_id=request.section_id,
            uuid=request.uuid,
            answer=answer,
            sources=_sources_to_snippets(sources),
            history=_history_to_messages(snapshot),
            query_filename=query_filename,
        )
        holder["response"] = resp
        logger.info(
            "graph ask ok section_id=%s sources=%d history=%d answer_len=%d "
            "search_query=%r",
            request.section_id,
            len(resp.sources),
            len(resp.history),
            len(answer),
            search_query,
        )

    return AskStream(_chunks(), holder)


__all__ = ["ask", "AskStream", "release_ask_session"]
