"""检索：向量 / BM25 / hybrid（Search Pipeline）。"""

from __future__ import annotations

import logging
from typing import Any, Literal

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from backend.config import settings
from backend.rag.document.embed import embed_query
from backend.rag.opensearch.client import get_opensearch_client
from backend.rag.opensearch.schema import ensure_search_pipeline

logger = logging.getLogger("backend.rag.retrieve.search")

# 拉取索引全部字段，仅排除 embedding（向量体积大且前端不需要）
_SOURCE_EXCLUDES = {"excludes": ["embedding"]}


def _format_hits(resp: dict) -> list[dict]:
    hits: list[dict] = []
    for hit in resp["hits"]["hits"]:
        item = dict(hit["_source"])
        item.pop("embedding", None)
        item["_score"] = hit["_score"]
        hits.append(item)
    return hits


def vector_search(
    query: str,
    k: int | None = None,
    index_name: str | None = None,
) -> list[dict]:
    client = get_opensearch_client()
    index_name = index_name or settings.opensearch_index
    k = k or settings.retrieval_top_k
    query_vec = embed_query(query)
    body = {
        "size": k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_vec,
                    "k": k,
                }
            }
        },
        "_source": _SOURCE_EXCLUDES,
    }
    resp = client.search(index=index_name, body=body)
    return _format_hits(resp)


def bm25_search(
    query: str,
    k: int | None = None,
    index_name: str | None = None,
) -> list[dict]:
    client = get_opensearch_client()
    index_name = index_name or settings.opensearch_index
    k = k or settings.retrieval_top_k
    body = {
        "size": k,
        "query": {"match": {"text": {"query": query}}},
        "_source": _SOURCE_EXCLUDES,
    }
    resp = client.search(index=index_name, body=body)
    return _format_hits(resp)


def hybrid_search(
    query: str,
    k: int | None = None,
    index_name: str | None = None,
    *,
    pipeline_name: str | None = None,
) -> list[dict]:
    """使用 OpenSearch hybrid query + Search Pipeline（normalization-processor）。"""
    client = get_opensearch_client()
    index_name = index_name or settings.opensearch_index
    k = k or settings.retrieval_top_k
    pipeline = pipeline_name or settings.hybrid_pipeline_name
    ensure_search_pipeline(pipeline)

    query_vec = embed_query(query)
    body = {
        "size": k,
        "query": {
            "hybrid": {
                "queries": [
                    {"match": {"text": {"query": query}}},
                    {
                        "knn": {
                            "embedding": {
                                "vector": query_vec,
                                "k": max(k * 4, k),
                            }
                        }
                    },
                ]
            }
        },
        "_source": _SOURCE_EXCLUDES,
    }
    # search_pipeline 走查询参数，配合 normalization-processor
    logger.info(
        "hybrid_search index=%s k=%d pipeline=%s query_len=%d",
        index_name,
        k,
        pipeline,
        len(query),
    )
    try:
        resp = client.search(
            index=index_name,
            body=body,
            params={"search_pipeline": pipeline},
        )
        hits = _format_hits(resp)
        logger.info("hybrid_search ok hits=%d", len(hits))
        return hits
    except Exception:
        logger.exception("hybrid_search failed index=%s", index_name)
        raise


class OpenSearchRetriever(BaseRetriever):
    mode: Literal["vector", "bm25", "hybrid"] = "hybrid"
    k: int = 10
    index_name: str | None = None

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        if self.mode == "vector":
            hits = vector_search(query, k=self.k, index_name=self.index_name)
        elif self.mode == "bm25":
            hits = bm25_search(query, k=self.k, index_name=self.index_name)
        else:
            hits = hybrid_search(query, k=self.k, index_name=self.index_name)

        return hits_to_documents(hits)


def get_retriever(
    mode: Literal["vector", "bm25", "hybrid"] = "hybrid",
    k: int | None = None,
    **kwargs,
) -> OpenSearchRetriever:
    return OpenSearchRetriever(
        mode=mode,
        k=k or settings.retrieval_top_k,
        **kwargs,
    )


def hits_to_documents(hits: list[dict]) -> list[Document]:
    """text → page_content；其余索引字段（除 embedding）全部进 metadata。"""
    docs: list[Document] = []
    for h in hits:
        text = str(h.get("text") or "")
        meta: dict = {}
        for key, value in h.items():
            if key in ("text", "embedding", "_score"):
                continue
            meta[key] = value
        if "_score" in h:
            meta["score"] = h["_score"]
        docs.append(Document(page_content=text, metadata=meta))
    return docs


def search_insight_text(
    query: str,
    *,
    uuid: str | None = None,
    index_name: str | None = None,
    recall_k: int | None = None,
) -> str:
    """洞察索引：混合检索 + 精排，只返回一条 chunk 的 text；无结果返回空串。

    若传入 ``uuid``，在 BM25 / knn 两侧加 document_id 过滤。
    """
    from backend.rag.retrieve.rerank import rerank_docs

    query = (query or "").strip()
    if not query:
        return ""
    client = get_opensearch_client()
    index_name = index_name or settings.opensearch_insight_index
    if not client.indices.exists(index=index_name):
        return ""

    k = recall_k or settings.retrieval_top_k
    pipeline = settings.hybrid_pipeline_name
    ensure_search_pipeline(pipeline)
    query_vec = embed_query(query)
    doc_filter = {"term": {"document_id": uuid}} if uuid else None

    bm25_q: dict[str, Any]
    knn_q: dict[str, Any]
    if doc_filter is not None:
        bm25_q = {
            "bool": {
                "must": {"match": {"text": {"query": query}}},
                "filter": [doc_filter],
            }
        }
        knn_q = {
            "knn": {
                "embedding": {
                    "vector": query_vec,
                    "k": max(k * 4, k),
                    "filter": doc_filter,
                }
            }
        }
    else:
        bm25_q = {"match": {"text": {"query": query}}}
        knn_q = {
            "knn": {
                "embedding": {
                    "vector": query_vec,
                    "k": max(k * 4, k),
                }
            }
        }

    body = {
        "size": k,
        "query": {"hybrid": {"queries": [bm25_q, knn_q]}},
        "_source": _SOURCE_EXCLUDES,
    }
    try:
        resp = client.search(
            index=index_name,
            body=body,
            params={"search_pipeline": pipeline},
        )
    except Exception:
        logger.exception("search_insight failed index=%s uuid=%s", index_name, uuid)
        raise

    hits = _format_hits(resp)
    docs = rerank_docs(query, hits_to_documents(hits), top_n=1)
    if not docs:
        return ""
    return str(docs[0].page_content or "")


def _hybrid_filtered_hits(
    query: str,
    *,
    index_name: str,
    filters: list[dict[str, Any]],
    recall_k: int,
) -> list[dict]:
    """带 filter 的 hybrid 检索，返回 hits（未精排）。"""
    client = get_opensearch_client()
    if not client.indices.exists(index=index_name):
        return []
    pipeline = settings.hybrid_pipeline_name
    ensure_search_pipeline(pipeline)
    query_vec = embed_query(query)
    bm25_q: dict[str, Any] = {
        "bool": {
            "must": {"match": {"text": {"query": query}}},
            "filter": filters,
        }
    }
    knn_q: dict[str, Any] = {
        "knn": {
            "embedding": {
                "vector": query_vec,
                "k": max(recall_k * 4, recall_k),
                "filter": {"bool": {"filter": filters}},
            }
        }
    }
    body = {
        "size": recall_k,
        "query": {"hybrid": {"queries": [bm25_q, knn_q]}},
        "_source": _SOURCE_EXCLUDES,
    }
    resp = client.search(
        index=index_name,
        body=body,
        params={"search_pipeline": pipeline},
    )
    return _format_hits(resp)


def search_section_insight_text(
    query: str,
    *,
    uuid: str,
    section_id: str,
    index_name: str | None = None,
    recall_k: int | None = None,
) -> str:
    """会话属性索引：混合检索 + 精排，返回最优一条 text。"""
    from backend.rag.retrieve.rerank import rerank_docs

    query = (query or "").strip()
    uuid = (uuid or "").strip()
    section_id = (section_id or "").strip()
    if not query or not uuid or not section_id:
        return ""
    index_name = index_name or settings.opensearch_section_insight_index
    k = recall_k or settings.retrieval_top_k
    filters = [
        {"term": {"document_id": uuid}},
        {"term": {"section_id": section_id}},
    ]
    try:
        hits = _hybrid_filtered_hits(
            query, index_name=index_name, filters=filters, recall_k=k
        )
    except Exception:
        logger.exception(
            "search_section_insight failed index=%s uuid=%s section_id=%s",
            index_name,
            uuid,
            section_id,
        )
        raise
    docs = rerank_docs(query, hits_to_documents(hits), top_n=1)
    if not docs:
        return ""
    return str(docs[0].page_content or "")


def search_section_document_texts(
    query: str,
    *,
    uuid: str,
    section_id: str,
    filename: str | None = None,
    top_n: int | None = None,
    index_name: str | None = None,
    recall_k: int | None = None,
) -> list[str]:
    """会话文档索引：混合检索 + 精排，返回至多 top_n 条 chunk text。"""
    from backend.rag.retrieve.rerank import rerank_docs

    query = (query or "").strip()
    uuid = (uuid or "").strip()
    section_id = (section_id or "").strip()
    if not query or not uuid or not section_id:
        return []
    index_name = index_name or settings.opensearch_section_document_index
    n = settings.section_document_top_n if top_n is None else int(top_n)
    if n < 1:
        return []
    k = recall_k or settings.retrieval_top_k
    filters: list[dict[str, Any]] = [
        {"term": {"document_id": uuid}},
        {"term": {"section_id": section_id}},
    ]
    if filename:
        filters.append({"term": {"source_file": filename.strip()}})
    try:
        hits = _hybrid_filtered_hits(
            query, index_name=index_name, filters=filters, recall_k=k
        )
    except Exception:
        logger.exception(
            "search_section_document failed index=%s uuid=%s section_id=%s",
            index_name,
            uuid,
            section_id,
        )
        raise
    docs = rerank_docs(query, hits_to_documents(hits), top_n=n)
    return [
        str(d.page_content or "") for d in docs if str(d.page_content or "").strip()
    ]
