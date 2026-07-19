"""检索上下文：format_docs + retrieve/rerank。"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.documents import Document

from backend.config import settings
from backend.llm.rephrase.rewrite import rewrite_query
from backend.rag.retrieve import get_retriever, rerank_docs

logger = logging.getLogger("backend.llm.pipeline.context")


def _meta_without_embedding(meta: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in meta.items() if k != "embedding"}


def _docs_payload(docs: list[Document]) -> list[dict[str, Any]]:
    """日志用：完整 chunk 正文 + 元字段（不含 embedding）。"""
    return [
        {
            "content": doc.page_content,
            "metadata": _meta_without_embedding(dict(doc.metadata)),
        }
        for doc in docs
    ]


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
    docs = retrieve_rerank_docs(inputs)
    return format_docs(docs)


def retrieve_rerank_docs(inputs: dict) -> list[Document]:
    """同 retrieve_rerank_context，但返回 Document 列表（供带来源回答）。"""
    query = inputs["query"]
    history = inputs.get("history") or []
    search_query = rewrite_query(query, history)
    logger.info(
        "retrieve query_before=%r query_after=%r history_msgs=%d",
        query,
        search_query,
        len(history),
    )

    retriever = get_retriever(mode="hybrid", k=settings.retrieval_top_k)
    docs = retriever.invoke(search_query)
    ranked = rerank_docs(search_query, docs, top_n=settings.rerank_top_n)
    logger.info(
        "retrieve_rerank chunks=%s",
        json.dumps(_docs_payload(ranked), ensure_ascii=False, default=str),
    )
    return ranked
