"""检索：向量 / BM25 / hybrid（Search Pipeline）。"""

from __future__ import annotations

import logging
from typing import Literal

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
