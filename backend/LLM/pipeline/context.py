"""检索上下文：format_docs + retrieve/rerank。"""

from __future__ import annotations

from langchain_core.documents import Document

from backend.LLM.rephrase.rewrite import rewrite_query
from backend.RAG.retrieve import get_retriever, rerank_docs
from backend.config import settings


def format_docs(docs: list[Document]) -> str:
    parts: list[str] = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source_file", "未知")
        chunk_idx = doc.metadata.get("chunk_index", "-")
        parts.append(
            f"[片段 {i}] （来源：{source}，chunk#{chunk_idx}）\n{doc.page_content}"
        )
    return "\n\n".join(parts)


def retrieve_rerank_context(inputs: dict) -> str:
    """检索 + rerank：使用改写后的 query；生成仍用原 query。"""
    query = inputs["query"]
    history = inputs.get("history") or []
    search_query = rewrite_query(query, history)

    retriever = get_retriever(mode="hybrid", k=settings.retrieval_top_k)
    docs = retriever.invoke(search_query)
    return format_docs(rerank_docs(search_query, docs, top_n=settings.rerank_top_n))


def retrieve_rerank_docs(inputs: dict) -> list[Document]:
    """同 retrieve_rerank_context，但返回 Document 列表（供带来源回答）。"""
    query = inputs["query"]
    history = inputs.get("history") or []
    search_query = rewrite_query(query, history)

    retriever = get_retriever(mode="hybrid", k=settings.retrieval_top_k)
    docs = retriever.invoke(search_query)
    return rerank_docs(search_query, docs, top_n=settings.rerank_top_n)
