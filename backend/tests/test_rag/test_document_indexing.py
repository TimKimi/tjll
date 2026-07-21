"""document.indexing 单元测试（mock OpenSearch / embed）。"""

from __future__ import annotations


def test_make_document_id_is_business_id():
    from backend.rag.document.indexing import make_document_id

    assert make_document_id("biz-abc") == "biz-abc"
    assert make_document_id("biz-abc") == make_document_id("biz-abc")


def test_make_chunk_id_format_and_stable():
    from backend.rag.document.indexing import make_chunk_id

    assert make_chunk_id("B1", "positive", 0) == "B1_pos_0000"
    assert make_chunk_id("B1", "negative", 12) == "B1_neg_0012"
    assert make_chunk_id("B1", "positive", 0) == make_chunk_id("B1", "positive", 0)


def test_build_chunk_docs_legacy_pdf_defaults():
    from backend.rag.document.indexing import (
        build_chunk_docs,
        make_chunk_id,
        make_document_id,
    )

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
    assert docs[0]["document_id"] == make_document_id("report")
    assert docs[0]["polarity"] == "positive"
    assert docs[0]["is_last_chunk"] is False
    assert docs[1]["is_last_chunk"] is True
    assert docs[0]["chunk_id"] == make_chunk_id("report", "positive", 0)
    assert docs[1]["chunk_id"] == make_chunk_id("report", "positive", 1)
    assert "created_at" in docs[0]


def test_build_yelp_chunk_docs_polarity_and_last_flag():
    from backend.rag.document.indexing import build_yelp_chunk_docs, make_chunk_id

    business = {
        "id": "biz1",
        "alias": "a",
        "name": "N",
        "categories": '[{"alias":"cafes"}]',
        "address": "{}",
        "hours": None,
        "is_closed": False,
        "review_count": 1,
        "rating": 4.0,
        "latitude": 1.0,
        "longitude": 2.0,
    }
    docs = build_yelp_chunk_docs(
        business,
        "negative",
        chunks=["n0", "n1", "n2"],
        embeddings=[[0.1], [0.2], [0.3]],
    )
    assert len(docs) == 3
    assert all(d["polarity"] == "negative" for d in docs)
    assert docs[0]["chunk_id"] == make_chunk_id("biz1", "negative", 0)
    assert docs[2]["is_last_chunk"] is True
    assert docs[0]["is_last_chunk"] is False
    assert docs[0]["document_id"] == "biz1"
    assert docs[0]["name"] == "N"


def test_normalize_business_fields_jsonish():
    from backend.rag.document.indexing import normalize_business_fields

    raw = {
        "id": "x",
        "alias": "al",
        "name": "nm",
        "categories": '[{"alias": "pizza", "title": "Pizza"}]',
        "address": '{"city": "Phx"}',
        "hours": {"Monday": "9-5"},
        "is_closed": False,
        "review_count": 3,
        "rating": 4.5,
        "latitude": 33.1,
        "longitude": -112.0,
        "image_url": None,
        "price": "$$",
    }
    out = normalize_business_fields(raw)
    assert out["categories"] == '[{"alias":"pizza","title":"Pizza"}]'
    assert out["address"] == '{"city":"Phx"}'
    assert out["hours"] == '{"Monday":"9-5"}'
    assert out["price"] == "$$"
    assert "clean_meta" not in out
    assert "positive_summary" not in out


def test_index_chunks_to_opensearch(monkeypatch):
    import backend.rag.document.indexing as idx

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
    import backend.rag.document.indexing as idx

    monkeypatch.setattr(idx, "ensure_index", lambda name=None: "idx")
    monkeypatch.setattr(idx, "load_document_as_text", lambda _p: "   ")
    monkeypatch.setattr(idx, "clean_text", lambda t: "")

    out = idx.index_file_to_opensearch("a.md", ensure=True)
    assert out == {"chunks": 0, "success": 0, "errors": []}


def test_index_file_to_opensearch_happy_path(monkeypatch):
    import backend.rag.document.indexing as idx

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
    assert out["document_id"] == "report"


def test_index_file_skips_ensure(monkeypatch):
    import backend.rag.document.indexing as idx

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


def test_index_business_summaries_splits_polarities(monkeypatch):
    """好评/坏评分开切分，分两次 bulk，不跨侧拼接。"""
    import backend.rag.document.indexing as idx

    def fake_split(text: str, chunk_size=None, chunk_overlap=None):
        if "POS" in text:
            return ["POS_A", "POS_B"]
        if "NEG" in text:
            return ["NEG_A"]
        return [text]

    def fake_embed(chunks: list[str]):
        return [[float(i)] for i in range(len(chunks))]

    captured: list[list[dict]] = []

    def fake_bulk(docs, index_name=None):
        captured.append(docs)
        return (len(docs), [])

    monkeypatch.setattr(idx, "split_text_to_chunks", fake_split)
    monkeypatch.setattr(idx, "embed_chunks", fake_embed)
    monkeypatch.setattr(idx, "index_chunks_to_opensearch", fake_bulk)

    raw = {
        "id": "bizX",
        "alias": "ax",
        "name": "Biz X",
        "positive_summary": "POS text",
        "negative_summary": "NEG text",
        "categories": "[]",
        "address": "{}",
        "hours": None,
        "is_closed": False,
        "review_count": 1,
        "rating": 5.0,
        "clean_meta": {"should": "not_index"},
    }
    out = idx.index_business_summaries_to_opensearch(raw, ensure=False)
    assert out["chunks"] == 3
    assert out["success"] == 3
    assert out["positive_chunks"] == 2
    assert out["negative_chunks"] == 1
    assert out["both_sides_complete"] is True
    assert len(captured) == 2
    pos_docs, neg_docs = captured
    assert all(d["polarity"] == "positive" for d in pos_docs)
    assert all(d["polarity"] == "negative" for d in neg_docs)
    assert pos_docs[0]["chunk_id"] == "bizX_pos_0000"
    assert pos_docs[1]["chunk_id"] == "bizX_pos_0001"
    assert pos_docs[1]["is_last_chunk"] is True
    assert neg_docs[0]["chunk_id"] == "bizX_neg_0000"
    assert neg_docs[0]["text"] == "NEG_A"
    assert pos_docs[1]["text"] == "POS_B"
    assert "clean_meta" not in pos_docs[0]


def test_index_business_pos_error_skips_neg(monkeypatch):
    import backend.rag.document.indexing as idx

    monkeypatch.setattr(idx, "split_text_to_chunks", lambda t, **k: [t])
    monkeypatch.setattr(idx, "embed_chunks", lambda chunks: [[0.1] for _ in chunks])

    calls = {"n": 0}

    def fake_bulk(docs, index_name=None):
        calls["n"] += 1
        if docs[0]["polarity"] == "positive":
            return (0, [{"error": "fail"}])
        return (len(docs), [])

    monkeypatch.setattr(idx, "index_chunks_to_opensearch", fake_bulk)

    out = idx.index_business_summaries_to_opensearch(
        {
            "id": "bizY",
            "positive_summary": "pos",
            "negative_summary": "neg",
            "alias": "",
            "name": "n",
        },
        ensure=False,
    )
    assert calls["n"] == 1
    assert out["both_sides_complete"] is False
    assert out["errors"]
    assert out["negative_chunks"] == 0


def test_index_business_neg_error_after_pos(monkeypatch):
    import backend.rag.document.indexing as idx

    monkeypatch.setattr(idx, "split_text_to_chunks", lambda t, **k: [t])
    monkeypatch.setattr(idx, "embed_chunks", lambda chunks: [[0.1] for _ in chunks])

    def fake_bulk(docs, index_name=None):
        if docs[0]["polarity"] == "negative":
            return (0, [{"error": "neg_fail"}])
        return (len(docs), [])

    monkeypatch.setattr(idx, "index_chunks_to_opensearch", fake_bulk)

    out = idx.index_business_summaries_to_opensearch(
        {
            "id": "bizN",
            "positive_summary": "pos",
            "negative_summary": "neg",
            "alias": "",
            "name": "n",
        },
        ensure=False,
    )
    assert out["positive_chunks"] == 1
    assert out["negative_chunks"] == 1
    assert out["both_sides_complete"] is False
    assert out["errors"]


def test_index_business_empty_summaries(monkeypatch):
    import backend.rag.document.indexing as idx

    monkeypatch.setattr(
        idx,
        "index_chunks_to_opensearch",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no bulk")),
    )
    out = idx.index_business_summaries_to_opensearch(
        {"id": "e", "positive_summary": "", "negative_summary": "  "},
        ensure=False,
    )
    assert out["chunks"] == 0
    assert out["success"] == 0
    assert out["both_sides_complete"] is False
