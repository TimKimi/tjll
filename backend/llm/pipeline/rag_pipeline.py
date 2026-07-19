"""对外一条龙：query + section_id → 回答。"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from backend.llm.client.llm import get_llm
from backend.llm.pipeline.chains import build_full_rag_chain
from backend.llm.pipeline.context import format_docs, retrieve_rerank_docs
from backend.llm.prompts.rag import RAG_PROMPT_WITH_HISTORY
from backend.llm.session.history import get_history
from backend.logging_setup import setup_app_logging

logger = logging.getLogger("backend.llm.pipeline.rag_pipeline")


@dataclass
class RagAnswer:
    """带来源与历史快照的 RAG 回答。"""

    answer: str
    query: str
    section_id: str
    sources: list[dict] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)


def _session_config(section_id: str) -> dict:
    """section_id 映射为 LangChain configurable.session_id。"""
    return {"configurable": {"session_id": section_id}}


def _sources_from_docs(docs: list[Document]) -> list[dict]:
    return [
        {
            "content": doc.page_content,
            "metadata": {
                k: v for k, v in dict(doc.metadata).items() if k != "embedding"
            },
        }
        for doc in docs
    ]


def _history_snapshot(messages: Sequence[BaseMessage]) -> list[dict]:
    """本轮写入前的历史 → [{role, content}, ...]。"""
    out: list[dict] = []
    for msg in messages:
        content = str(getattr(msg, "content", "") or "")
        if isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        elif isinstance(msg, SystemMessage):
            role = "system"
        else:
            role = "system"
        out.append({"role": role, "content": content})
    return out


def _json_log(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


def answer_query(query: str, section_id: str) -> str:
    """非流式完整 RAG 回答（重述 + 检索 + rerank + Redis 历史）。"""
    setup_app_logging()
    logger.info("answer_query section_id=%s query_len=%d", section_id, len(query))
    try:
        chain = build_full_rag_chain()
        return chain.invoke({"query": query}, config=_session_config(section_id))
    except Exception:
        logger.exception("answer_query failed section_id=%s", section_id)
        raise


def stream_answer_query(query: str, section_id: str) -> Iterator[str]:
    """流式完整 RAG 回答。"""
    setup_app_logging()
    logger.info(
        "stream_answer_query section_id=%s query_len=%d", section_id, len(query)
    )
    try:
        chain = build_full_rag_chain()
        yield from chain.stream({"query": query}, config=_session_config(section_id))
    except Exception:
        logger.exception("stream_answer_query failed section_id=%s", section_id)
        raise


def answer_query_with_sources(query: str, section_id: str) -> RagAnswer:
    """完整 RAG 回答，并返回精排后的资料片段 + 写入前历史快照。"""
    setup_app_logging()
    logger.info(
        "answer_query_with_sources start section_id=%s query=%r",
        section_id,
        query,
    )
    try:
        history = get_history(section_id)
        hist_msgs = list(history.messages)
        hist_snapshot = _history_snapshot(hist_msgs)
        logger.info(
            "history_before_write section_id=%s messages=%s",
            section_id,
            _json_log(hist_snapshot),
        )
        docs = retrieve_rerank_docs({"query": query, "history": hist_msgs})
        sources = _sources_from_docs(docs)
        logger.info(
            "sources_used section_id=%s chunks=%s",
            section_id,
            _json_log(sources),
        )
        llm = get_llm(temperature=0.2)
        answer = (RAG_PROMPT_WITH_HISTORY | llm | StrOutputParser()).invoke(
            {
                "context": format_docs(docs),
                "query": query,
                "history": hist_msgs,
            }
        )
        history.add_user_message(query)
        history.add_ai_message(answer)
        logger.info(
            "answer_query_with_sources ok section_id=%s answer=%r",
            section_id,
            answer,
        )
        return RagAnswer(
            answer=answer,
            query=query,
            section_id=section_id,
            sources=sources,
            history=hist_snapshot,
        )
    except Exception:
        logger.exception(
            "answer_query_with_sources failed section_id=%s",
            section_id,
        )
        raise
