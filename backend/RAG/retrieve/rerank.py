"""Rerank：FlagEmbedding bge-reranker（无 Redis / 无查询重述）。"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.documents import Document

from backend.config import settings


@lru_cache(maxsize=1)
def get_reranker():
    from FlagEmbedding import FlagReranker

    use_fp16 = settings.rerank_use_fp16 and settings.embedding_device == "cuda"
    return FlagReranker(settings.rerank_model_dir, use_fp16=use_fp16)


def rerank_docs(
    query: str,
    docs: list[Document],
    top_n: int | None = None,
) -> list[Document]:
    if not docs:
        return docs

    top_n = top_n or settings.rerank_top_n
    reranker = get_reranker()
    pairs = [(query, d.page_content) for d in docs]
    scores = reranker.compute_score(pairs, normalize=True)
    if isinstance(scores, float):
        scores = [scores]

    scored = sorted(zip(scores, docs, strict=True), key=lambda x: x[0], reverse=True)
    out: list[Document] = []
    for score, doc in scored[:top_n]:
        meta = dict(doc.metadata)
        meta["rerank_score"] = float(score)
        out.append(Document(page_content=doc.page_content, metadata=meta))
    return out


def hybrid_search_with_rerank(
    query: str,
    *,
    recall_k: int | None = None,
    top_n: int | None = None,
    index_name: str | None = None,
) -> list[Document]:
    """hybrid（Search Pipeline）粗排 + FlagEmbedding 精排。"""
    from backend.RAG.retrieve.search import hybrid_search, hits_to_documents

    hits = hybrid_search(
        query,
        k=recall_k or settings.retrieval_top_k,
        index_name=index_name,
    )
    return rerank_docs(query, hits_to_documents(hits), top_n=top_n)
