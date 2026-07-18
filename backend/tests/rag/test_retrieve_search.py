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
                        "document_id": "d1",
                        "source_file": "a.pdf",
                        "chunk_index": 0,
                        "text": "内容A",
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

    docs = search_mod.hits_to_documents(hits)
    assert isinstance(docs[0], Document)
    assert docs[0].page_content == "内容A"
    assert docs[0].metadata["chunk_id"] == "c1"
    assert docs[0].metadata["score"] == 1.5


def test_hits_to_documents_includes_yelp_meta():
    from backend.rag.retrieve.search import hits_to_documents

    docs = hits_to_documents(
        [
            {
                "text": "好评片段",
                "chunk_id": "b_pos_0000",
                "document_id": "b",
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


def test_source_fields_include_yelp_meta():
    from backend.rag.retrieve.search import _SOURCE_FIELDS

    for key in ("polarity", "is_last_chunk", "id", "name", "alias"):
        assert key in _SOURCE_FIELDS


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
    assert "knn" in client.last["body"]["query"]
    assert "polarity" in client.last["body"]["_source"]
    assert "name" in client.last["body"]["_source"]
    b = search_mod.bm25_search("q", k=2)
    assert b[0]["chunk_id"] == "c1"
    assert client.last["body"]["query"]["match"]["text"]["query"] == "q"

    h = search_mod.hybrid_search("q")
    assert h[0]["document_id"] == "d1"
    assert client.last["params"]["search_pipeline"] == "pipe"
    assert "hybrid" in client.last["body"]["query"]


def test_get_retriever_and_modes(monkeypatch):
    import backend.rag.retrieve.search as search_mod

    monkeypatch.setattr(
        search_mod,
        "vector_search",
        lambda query, k=None, index_name=None: [
            {
                "text": "v",
                "chunk_id": "1",
                "document_id": "d",
                "source_file": "f",
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
                "document_id": "d",
                "source_file": "f",
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
                "document_id": "d",
                "source_file": "f",
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
