"""RAG pipeline：query / uuid / section_id → 回答。"""

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
from backend.llm.session.history import get_history, make_history_session_id
from backend.logging_setup import setup_app_logging

logger = logging.getLogger("backend.llm.pipeline.rag_pipeline")


@dataclass
class RagAnswer:
    """含 sources 与 history 快照的回答。"""

    answer: str
    query: str
    section_id: str
    sources: list[dict] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)


def _session_config(uuid: str, section_id: str) -> dict:
    """构造 LangChain session_id 配置。"""
    return {"configurable": {"session_id": make_history_session_id(uuid, section_id)}}


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
    """消息列表转为 role/content 快照。"""
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


def answer_query(query: str, section_id: str, uuid: str) -> str:
    """非流式回答。"""
    setup_app_logging()
    logger.info(
        "answer_query uuid=%s section_id=%s query_len=%d",
        uuid,
        section_id,
        len(query),
    )
    try:
        chain = build_full_rag_chain()
        return chain.invoke({"query": query}, config=_session_config(uuid, section_id))
    except Exception:
        logger.exception("answer_query failed uuid=%s section_id=%s", uuid, section_id)
        raise


def stream_answer_query(query: str, section_id: str, uuid: str) -> Iterator[str]:
    """流式回答。"""
    setup_app_logging()
    logger.info(
        "stream_answer_query uuid=%s section_id=%s query_len=%d",
        uuid,
        section_id,
        len(query),
    )
    try:
        chain = build_full_rag_chain()
        yield from chain.stream(
            {"query": query}, config=_session_config(uuid, section_id)
        )
    except Exception:
        logger.exception(
            "stream_answer_query failed uuid=%s section_id=%s", uuid, section_id
        )
        raise


def answer_query_with_sources(query: str, section_id: str, uuid: str) -> RagAnswer:
    """非流式回答，附带 sources 与写入前 history。"""
    setup_app_logging()
    logger.info(
        "answer_query_with_sources start uuid=%s section_id=%s query=%r",
        uuid,
        section_id,
        query,
    )
    try:
        history = get_history(uuid, section_id)
        hist_msgs = list(history.messages)
        hist_snapshot = _history_snapshot(hist_msgs)
        logger.info(
            "history_before_write uuid=%s section_id=%s messages=%s",
            uuid,
            section_id,
            _json_log(hist_snapshot),
        )
        docs = retrieve_rerank_docs({"query": query, "history": hist_msgs})
        sources = _sources_from_docs(docs)
        logger.info(
            "sources_used uuid=%s section_id=%s chunks=%s",
            uuid,
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
            "answer_query_with_sources ok uuid=%s section_id=%s answer=%r",
            uuid,
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
            "answer_query_with_sources failed uuid=%s section_id=%s",
            uuid,
            section_id,
        )
        raise
