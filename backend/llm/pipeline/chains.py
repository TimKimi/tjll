"""LCEL RAG 链（移植自 shixun/rag.py，imports 使用 backend.*）。"""

from __future__ import annotations

from operator import itemgetter
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory

from backend.llm.client.llm import get_llm
from backend.llm.pipeline.context import format_docs, retrieve_rerank_context
from backend.llm.prompts.rag import RAG_PROMPT, RAG_PROMPT_WITH_HISTORY
from backend.llm.session.history import get_history
from backend.rag.retrieve import get_retriever, rerank_docs
from backend.config import settings


def build_rag_chain(k: int | None = None):
    """最简 RAG 链：混合检索 → prompt → LLM。"""
    retriever = get_retriever(mode="hybrid", k=k or settings.retrieval_top_k)
    llm = get_llm()

    return (
        {
            "context": RunnableLambda(lambda q: format_docs(retriever.invoke(q))),
            "query": RunnablePassthrough(),
        }
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )


def build_rag_chain_with_rerank(
    recall_k: int | None = None,
    top_n: int | None = None,
):
    """RAG 链 + rerank 精排。"""
    recall_k = recall_k or settings.retrieval_top_k
    top_n = top_n or settings.rerank_top_n
    retriever = get_retriever(mode="hybrid", k=recall_k)
    llm = get_llm()

    retrieve_and_rerank: Any = RunnableLambda(
        lambda q: format_docs(rerank_docs(q, retriever.invoke(q), top_n=top_n))
    )

    return (
        {
            "context": retrieve_and_rerank,
            "query": RunnablePassthrough(),
        }
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )


def build_rag_chain_with_history(
    recall_k: int | None = None,
    top_n: int | None = None,
):
    """RAG 链 + rerank + Redis 多轮历史（不含查询重述）。"""
    recall_k = recall_k or settings.retrieval_top_k
    top_n = top_n or settings.rerank_top_n
    retriever = get_retriever(mode="hybrid", k=recall_k)
    llm = get_llm()

    retrieve_and_rerank: Any = RunnableLambda(
        lambda x: format_docs(
            rerank_docs(
                x["query"],
                retriever.invoke(x["query"]),
                top_n=top_n,
            )
        )
    )

    core_chain = (
        {
            "context": retrieve_and_rerank,
            "query": itemgetter("query"),
            "history": itemgetter("history"),
        }
        | RAG_PROMPT_WITH_HISTORY
        | llm
        | StrOutputParser()
    )

    return RunnableWithMessageHistory(
        core_chain,
        get_session_history=get_history,
        input_messages_key="query",
        history_messages_key="history",
    )


def build_full_rag_chain():
    """完整链：重述 → 检索 → rerank → 生成（检索用改写 query，生成用原 query）。"""
    llm = get_llm()

    core_chain = (
        {
            "context": RunnableLambda(retrieve_rerank_context),
            "query": itemgetter("query"),
            "history": itemgetter("history"),
        }
        | RAG_PROMPT_WITH_HISTORY
        | llm
        | StrOutputParser()
    )

    return RunnableWithMessageHistory(
        core_chain,
        get_session_history=get_history,
        input_messages_key="query",
        history_messages_key="history",
    )
