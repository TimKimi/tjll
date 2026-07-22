"""retrieve.search 单元测试（mock OpenSearch / embed）。"""

from __future__ import annotations

from langchain_core.documents import Document


def _fake_hits_resp():
    return {
        "hits": {
            "hits": [
                {
                    "_score": 1.5,
                    "_source": {
                        "chunk_id": "c1",
                        "id": "d1",
                        "name": "a.pdf",
                        "chunk_index": 0,
                        "text": "内容A",
                        "embedding": [0.1, 0.2, 0.3],
                    },
                }
            ]
        }
    }


def test_format_hits_and_hits_to_documents():
    from backend.rag.retrieve import search as search_mod

    hits = search_mod._format_hits(_fake_hits_resp())
    assert hits[0]["_score"] == 1.5
    assert hits[0]["text"] == "内容A"
    assert "embedding" not in hits[0]

    docs = search_mod.hits_to_documents(hits)
    assert isinstance(docs[0], Document)
    assert docs[0].page_content == "内容A"
    assert docs[0].metadata["chunk_id"] == "c1"
    assert docs[0].metadata["name"] == "a.pdf"
    assert docs[0].metadata["score"] == 1.5
    assert "embedding" not in docs[0].metadata
    assert "text" not in docs[0].metadata


def test_hits_to_documents_includes_yelp_meta():
    from backend.rag.retrieve.search import hits_to_documents

    docs = hits_to_documents(
        [
            {
                "text": "好评片段",
                "chunk_id": "b_pos_0000",
                "chunk_index": 0,
                "_score": 2.0,
                "polarity": "positive",
                "id": "b",
                "name": "Biz",
                "alias": "biz",
                "is_last_chunk": True,
            }
        ]
    )
    meta = docs[0].metadata
    assert meta["polarity"] == "positive"
    assert meta["name"] == "Biz"
    assert meta["alias"] == "biz"
    assert meta["id"] == "b"
    assert meta["is_last_chunk"] is True
    assert "source_file" not in meta
    assert "document_id" not in meta
    assert "embedding" not in meta


def test_retriever_tolerates_missing_source_file(monkeypatch):
    """Yelp chunk 无 source_file，Retriever 不得 KeyError。"""
    import backend.rag.retrieve.search as search_mod

    monkeypatch.setattr(
        search_mod,
        "hybrid_search",
        lambda query, k=None, index_name=None, pipeline_name=None: [
            {
                "text": "好吃",
                "chunk_id": "b_pos_0000",
                "id": "b",
                "chunk_index": 0,
                "_score": 1.2,
                "polarity": "positive",
                "name": "Acme",
            }
        ],
    )
    r = search_mod.OpenSearchRetriever(mode="hybrid", k=1)
    docs = r.invoke("q")
    assert docs[0].page_content == "好吃"
    assert "source_file" not in docs[0].metadata
    assert docs[0].metadata["name"] == "Acme"


def test_source_excludes_embedding_only():
    from backend.rag.retrieve.search import _SOURCE_EXCLUDES

    assert _SOURCE_EXCLUDES == {"excludes": ["embedding"]}


def test_vector_bm25_hybrid_search(monkeypatch):
    import backend.rag.retrieve.search as search_mod

    class FakeClient:
        def __init__(self) -> None:
            self.last: dict = {}

        def search(self, index=None, body=None, params=None):
            self.last = {"index": index, "body": body, "params": params}
            return _fake_hits_resp()

    client = FakeClient()
    monkeypatch.setattr(search_mod, "get_opensearch_client", lambda: client)
    monkeypatch.setattr(search_mod, "embed_query", lambda q: [0.1, 0.2])
    monkeypatch.setattr(search_mod, "ensure_search_pipeline", lambda name=None: "pipe")
    monkeypatch.setattr(search_mod.settings, "opensearch_index", "idx")
    monkeypatch.setattr(search_mod.settings, "retrieval_top_k", 3)
    monkeypatch.setattr(search_mod.settings, "hybrid_pipeline_name", "pipe")

    v = search_mod.vector_search("q")
    assert v[0]["text"] == "内容A"
    assert "embedding" not in v[0]
    assert "knn" in client.last["body"]["query"]
    assert client.last["body"]["_source"] == {"excludes": ["embedding"]}

    b = search_mod.bm25_search("q", k=2)
    assert b[0]["chunk_id"] == "c1"
    assert client.last["body"]["query"]["match"]["text"]["query"] == "q"
    assert client.last["body"]["_source"] == {"excludes": ["embedding"]}

    h = search_mod.hybrid_search("q")
    assert h[0]["id"] == "d1"
    assert client.last["params"]["search_pipeline"] == "pipe"
    assert "hybrid" in client.last["body"]["query"]
    assert client.last["body"]["_source"] == {"excludes": ["embedding"]}


def test_get_retriever_and_modes(monkeypatch):
    import backend.rag.retrieve.search as search_mod

    monkeypatch.setattr(
        search_mod,
        "vector_search",
        lambda query, k=None, index_name=None: [
            {
                "text": "v",
                "chunk_id": "1",
                "id": "d",
                "name": "f",
                "chunk_index": 0,
                "_score": 1.0,
            }
        ],
    )
    monkeypatch.setattr(
        search_mod,
        "bm25_search",
        lambda query, k=None, index_name=None: [
            {
                "text": "b",
                "chunk_id": "2",
                "id": "d",
                "name": "f",
                "chunk_index": 1,
                "_score": 2.0,
            }
        ],
    )
    monkeypatch.setattr(
        search_mod,
        "hybrid_search",
        lambda query, k=None, index_name=None, pipeline_name=None: [
            {
                "text": "h",
                "chunk_id": "3",
                "id": "d",
                "name": "f",
                "chunk_index": 2,
                "_score": 3.0,
            }
        ],
    )
    monkeypatch.setattr(search_mod.settings, "retrieval_top_k", 5)

    r = search_mod.get_retriever(mode="vector", k=1)
    assert r.mode == "vector"
    assert r.invoke("q")[0].page_content == "v"

    r2 = search_mod.OpenSearchRetriever(mode="bm25", k=1)
    assert r2.invoke("q")[0].page_content == "b"

    r3 = search_mod.OpenSearchRetriever(mode="hybrid", k=1)
    assert r3.invoke("q")[0].page_content == "h"
    assert r3.invoke("q")[0].metadata["score"] == 3.0
