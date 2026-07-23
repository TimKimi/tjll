"""Ask 图节点实现。"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from backend.config import settings
from backend.llm.graph.session_pool import get_session_pool
from backend.llm.graph.state import AskState
from backend.llm.graph.tools import sources_from_docs
from backend.llm.pipeline.context import format_docs
from backend.llm.rephrase.rewrite import rewrite_query
from backend.rag.retrieve import get_retriever, rerank_docs

logger = logging.getLogger("backend.llm.graph.nodes")


def history_snapshot(messages: Sequence[BaseMessage]) -> list[dict[str, Any]]:
    """历史 → 对外快照 dict（含 search_query / filename / sources）。"""
    out: list[dict[str, Any]] = []
    for msg in messages:
        content = str(getattr(msg, "content", "") or "")
        extra = dict(getattr(msg, "additional_kwargs", None) or {})
        if isinstance(msg, HumanMessage):
            role = "user"
            item: dict[str, Any] = {
                "role": role,
                "content": content,
                "search_query": extra.get("search_query"),
                "filename": extra.get("filename") or "",
                "insight_create": bool(extra.get("insight_create", False)),
                "insight_use": bool(extra.get("insight_use", False)),
                "used": bool(extra.get("used", False)),
                "sources": None,
            }
        elif isinstance(msg, AIMessage):
            role = "assistant"
            item = {
                "role": role,
                "content": content,
                "search_query": None,
                "filename": None,
                "insight_create": None,
                "insight_use": None,
                "used": bool(extra.get("used", False)),
                "sources": extra.get("sources") or [],
            }
        elif isinstance(msg, SystemMessage):
            item = {
                "role": "system",
                "content": content,
                "search_query": None,
                "filename": None,
                "insight_create": None,
                "insight_use": None,
                "used": bool(extra.get("used", False)),
                "sources": None,
            }
        else:
            item = {
                "role": "system",
                "content": content,
                "search_query": None,
                "filename": None,
                "insight_create": None,
                "insight_use": None,
                "used": bool(extra.get("used", False)),
                "sources": None,
            }
        out.append(item)
    return out


def prepare(state: AskState) -> dict[str, Any]:
    """校验入参；补齐缺省字段。"""
    query = (state.get("query") or "").strip()
    section_id = (state.get("section_id") or "").strip()
    uuid = (state.get("uuid") or "").strip()
    if not query:
        raise ValueError("query is required")
    if not section_id:
        raise ValueError("section_id is required")
    if not uuid:
        raise ValueError("uuid is required")
    history = list(state.get("history") or [])
    logger.info(
        "prepare uuid=%s section_id=%s history_msgs=%d query_len=%d",
        uuid,
        section_id,
        len(history),
        len(query),
    )
    return {
        "query": query,
        "section_id": section_id,
        "uuid": uuid,
        "insight_create": bool(state.get("insight_create", False)),
        "insight_use": bool(state.get("insight_use", False)),
        "history": history,
        "search_query": query,
    }


def rewrite(state: AskState) -> dict[str, Any]:
    """结合历史重述检索 query；生成仍用原 query。"""
    query = state["query"]
    history = state.get("history") or []
    search_query = rewrite_query(query, history)
    return {"search_query": search_query}


def retrieve_rerank(state: AskState) -> dict[str, Any]:
    """混合检索 + rerank；context 进 State，sources/search_query 写入会话侧车。"""
    search_query = state.get("search_query") or state["query"]
    retriever = get_retriever(mode="hybrid", k=settings.retrieval_top_k)
    docs = retriever.invoke(search_query)
    ranked = rerank_docs(search_query, docs, top_n=settings.rerank_top_n)

    sources = sources_from_docs(ranked)
    uuid = (state.get("uuid") or "").strip()
    section_id = (state.get("section_id") or "").strip()
    if not uuid or not section_id:
        raise ValueError("uuid and section_id are both required")
    session = get_session_pool().get_or_create(
        uuid,
        section_id,
        load_history=False,
    )
    session.last_sources = sources
    session.last_search_query = search_query
    session.touch()

    context = format_docs(ranked)
    logger.info(
        "retrieve_rerank section_id=%s search_query=%r sources=%d",
        state.get("section_id"),
        search_query,
        len(sources),
    )
    return {"context": context, "search_query": search_query}
