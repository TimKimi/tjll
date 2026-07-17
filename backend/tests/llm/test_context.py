"""LLM pipeline.context 单元测试（mock rewrite / retriever / rerank）。"""

from __future__ import annotations

from langchain_core.documents import Document


class _FakeRetriever:
    def __init__(self, docs=None):
        self.docs = docs or [
            Document(
                page_content="资料", metadata={"source_file": "a.pdf", "chunk_index": 0}
            )
        ]
        self.last_query = None

    def invoke(self, query, config=None):
        self.last_query = query
        return list(self.docs)


def test_retrieve_rerank_docs(monkeypatch):
    import backend.LLM.pipeline.context as ctx

    retriever = _FakeRetriever()
    monkeypatch.setattr(ctx, "rewrite_query", lambda q, h: f"改写:{q}")
    monkeypatch.setattr(ctx, "get_retriever", lambda mode="hybrid", k=10: retriever)
    monkeypatch.setattr(
        ctx,
        "rerank_docs",
        lambda query, docs, top_n=None: docs[:1],
    )
    monkeypatch.setattr(ctx.settings, "retrieval_top_k", 5)
    monkeypatch.setattr(ctx.settings, "rerank_top_n", 1)

    docs = ctx.retrieve_rerank_docs({"query": "原问题", "history": []})
    assert len(docs) == 1
    assert docs[0].page_content == "资料"
    assert retriever.last_query == "改写:原问题"


def test_retrieve_rerank_context(monkeypatch):
    import backend.LLM.pipeline.context as ctx

    retriever = _FakeRetriever(
        [
            Document(
                page_content="正文",
                metadata={"source_file": "b.pdf", "chunk_index": 2},
            )
        ]
    )
    monkeypatch.setattr(ctx, "rewrite_query", lambda q, h: q)
    monkeypatch.setattr(ctx, "get_retriever", lambda mode="hybrid", k=10: retriever)
    monkeypatch.setattr(
        ctx,
        "rerank_docs",
        lambda query, docs, top_n=None: docs,
    )
    monkeypatch.setattr(ctx.settings, "retrieval_top_k", 5)
    monkeypatch.setattr(ctx.settings, "rerank_top_n", 3)

    text = ctx.retrieve_rerank_context({"query": "问", "history": ["x"]})
    assert "正文" in text
    assert "b.pdf" in text
    assert "chunk#2" in text
