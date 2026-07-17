"""retrieve.rerank 单元测试（mock FlagEmbedding）。"""

from __future__ import annotations

from langchain_core.documents import Document


def test_rerank_docs_empty():
    from backend.RAG.retrieve.rerank import rerank_docs

    assert rerank_docs("q", []) == []


def test_rerank_docs_orders_by_score(monkeypatch):
    import backend.RAG.retrieve.rerank as rerank_mod

    class FakeReranker:
        def compute_score(self, pairs, normalize=True):
            # higher for second pair
            return [0.1, 0.9]

    monkeypatch.setattr(rerank_mod, "get_reranker", lambda: FakeReranker())
    monkeypatch.setattr(rerank_mod.settings, "rerank_top_n", 1)

    docs = [
        Document(page_content="低分", metadata={"chunk_index": 0}),
        Document(page_content="高分", metadata={"chunk_index": 1}),
    ]
    out = rerank_mod.rerank_docs("查询", docs, top_n=1)
    assert len(out) == 1
    assert out[0].page_content == "高分"
    assert out[0].metadata["rerank_score"] == 0.9


def test_rerank_docs_single_float_score(monkeypatch):
    import backend.RAG.retrieve.rerank as rerank_mod

    class FakeReranker:
        def compute_score(self, pairs, normalize=True):
            return 0.77

    monkeypatch.setattr(rerank_mod, "get_reranker", lambda: FakeReranker())

    docs = [Document(page_content="only", metadata={})]
    out = rerank_mod.rerank_docs("q", docs, top_n=1)
    assert out[0].metadata["rerank_score"] == 0.77


def test_hybrid_search_with_rerank(monkeypatch):
    import backend.RAG.retrieve.rerank as rerank_mod

    monkeypatch.setattr(
        "backend.RAG.retrieve.search.hybrid_search",
        lambda query, k=None, index_name=None: [
            {
                "text": "命中",
                "chunk_id": "c",
                "document_id": "d",
                "source_file": "s.pdf",
                "chunk_index": 0,
                "_score": 1.0,
            }
        ],
    )
    monkeypatch.setattr(
        rerank_mod,
        "rerank_docs",
        lambda query, docs, top_n=None: docs[:1],
    )
    monkeypatch.setattr(rerank_mod.settings, "retrieval_top_k", 5)

    out = rerank_mod.hybrid_search_with_rerank("q", top_n=1)
    assert len(out) == 1
    assert out[0].page_content == "命中"
