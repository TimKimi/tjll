"""对外一条龙：query + section_id → 回答。"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

from backend.LLM.client.llm import get_llm
from backend.LLM.pipeline.chains import build_full_rag_chain
from backend.LLM.pipeline.context import format_docs, retrieve_rerank_docs
from backend.LLM.prompts.rag import RAG_PROMPT_WITH_HISTORY
from backend.LLM.session.history import get_history


@dataclass
class RagAnswer:
    """带来源的 RAG 回答。"""

    answer: str
    query: str
    section_id: str
    sources: list[dict] = field(default_factory=list)


def _session_config(section_id: str) -> dict:
    """section_id 映射为 LangChain configurable.session_id。"""
    return {"configurable": {"session_id": section_id}}


def _sources_from_docs(docs: list[Document]) -> list[dict]:
    return [
        {"content": doc.page_content, "metadata": dict(doc.metadata)} for doc in docs
    ]


def answer_query(query: str, section_id: str) -> str:
    """非流式完整 RAG 回答（重述 + 检索 + rerank + Redis 历史）。"""
    chain = build_full_rag_chain()
    return chain.invoke({"query": query}, config=_session_config(section_id))


def stream_answer_query(query: str, section_id: str) -> Iterator[str]:
    """流式完整 RAG 回答。"""
    chain = build_full_rag_chain()
    yield from chain.stream({"query": query}, config=_session_config(section_id))


def answer_query_with_sources(query: str, section_id: str) -> RagAnswer:
    """完整 RAG 回答，并返回精排后的资料片段。"""
    history = get_history(section_id)
    hist_msgs = list(history.messages)
    docs = retrieve_rerank_docs({"query": query, "history": hist_msgs})
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
    return RagAnswer(
        answer=answer,
        query=query,
        section_id=section_id,
        sources=_sources_from_docs(docs),
    )
