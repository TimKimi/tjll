"""document.indexing 单元测试（mock OpenSearch / embed）。"""

from __future__ import annotations


def test_make_document_id_stable():
    from backend.RAG.document.indexing import make_document_id

    a = make_document_id("/path/to/a.pdf")
    b = make_document_id("/path/to/a.pdf")
    assert a == b
    assert len(a) == 12


def test_build_chunk_docs():
    from backend.RAG.document.indexing import build_chunk_docs, make_document_id

    docs = build_chunk_docs(
        "/data/report.pdf",
        chunks=["c0", "c1"],
        embeddings=[[0.1, 0.2], [0.3, 0.4]],
    )
    assert len(docs) == 2
    assert docs[0]["source_file"] == "report.pdf"
    assert docs[0]["chunk_index"] == 0
    assert docs[0]["text"] == "c0"
    assert docs[0]["embedding"] == [0.1, 0.2]
    assert docs[0]["document_id"] == make_document_id("/data/report.pdf")
    assert docs[0]["chunk_id"].endswith("_chunk_0000")
    assert docs[1]["chunk_id"].endswith("_chunk_0001")
    assert "created_at" in docs[0]


def test_index_chunks_to_opensearch(monkeypatch):
    import backend.RAG.document.indexing as idx

    class FakeIndices:
        def refresh(self, index=None):
            self.refreshed = index

    class FakeClient:
        def __init__(self):
            self.indices = FakeIndices()

    client = FakeClient()

    monkeypatch.setattr(idx, "get_opensearch_client", lambda: client)
    monkeypatch.setattr(
        idx,
        "bulk",
        lambda _c, actions, chunk_size=100: (len(list(actions)), []),
    )
    monkeypatch.setattr(idx.settings, "opensearch_index", "test-idx")

    docs = [
        {
            "chunk_id": "id0",
            "text": "t",
            "embedding": [1.0],
        }
    ]
    success, errors = idx.index_chunks_to_opensearch(docs)
    assert success == 1
    assert errors == []
    assert client.indices.refreshed == "test-idx"


def test_index_file_to_opensearch_empty_text(monkeypatch):
    import backend.RAG.document.indexing as idx

    monkeypatch.setattr(idx, "ensure_index", lambda name=None: "idx")
    monkeypatch.setattr(idx, "load_document_as_text", lambda _p: "   ")
    monkeypatch.setattr(idx, "clean_text", lambda t: "")

    out = idx.index_file_to_opensearch("a.md", ensure=True)
    assert out == {"chunks": 0, "success": 0, "errors": []}


def test_index_file_to_opensearch_happy_path(monkeypatch):
    import backend.RAG.document.indexing as idx

    monkeypatch.setattr(idx, "ensure_index", lambda name=None: "idx")
    monkeypatch.setattr(idx, "load_document_as_text", lambda _p: "hello world")
    monkeypatch.setattr(idx, "clean_text", lambda t: t)
    monkeypatch.setattr(idx, "split_text_to_chunks", lambda t: ["hello", "world"])
    monkeypatch.setattr(
        idx,
        "embed_chunks",
        lambda chunks: [[0.1], [0.2]],
    )
    monkeypatch.setattr(
        idx,
        "index_chunks_to_opensearch",
        lambda docs, index_name=None: (2, []),
    )

    out = idx.index_file_to_opensearch("report.md", ensure=True, index_name="idx")
    assert out["chunks"] == 2
    assert out["success"] == 2
    assert out["dims"] == 1
    assert out["errors"] == []
    assert "document_id" in out


def test_index_file_skips_ensure(monkeypatch):
    import backend.RAG.document.indexing as idx

    called = {"ensure": False}

    def boom(_name=None):
        called["ensure"] = True
        raise AssertionError("should not ensure")

    monkeypatch.setattr(idx, "ensure_index", boom)
    monkeypatch.setattr(idx, "load_document_as_text", lambda _p: "")
    monkeypatch.setattr(idx, "clean_text", lambda t: "")

    out = idx.index_file_to_opensearch("a.md", ensure=False)
    assert out["chunks"] == 0
    assert called["ensure"] is False
