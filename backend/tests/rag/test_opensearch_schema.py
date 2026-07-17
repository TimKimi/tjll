"""opensearch.schema 单元测试。"""

from __future__ import annotations


def test_index_mapping_body_structure():
    from backend.RAG.opensearch.schema import index_mapping_body

    body = index_mapping_body(dims=8)
    assert body["settings"]["index"]["knn"] is True
    props = body["mappings"]["properties"]
    assert props["embedding"]["dimension"] == 8
    assert props["text"]["analyzer"] == "ik_max_word"
    assert "ik_smart_analyzer" in body["settings"]["analysis"]["analyzer"]


def test_hybrid_pipeline_body_weights():
    from backend.RAG.opensearch.schema import hybrid_pipeline_body
    from backend.config import settings

    body = hybrid_pipeline_body()
    proc = body["phase_results_processors"][0]["normalization-processor"]
    assert proc["normalization"]["technique"] == "min_max"
    weights = proc["combination"]["parameters"]["weights"]
    assert weights == [settings.hybrid_bm25_weight, settings.hybrid_vector_weight]


def test_ensure_search_pipeline(monkeypatch):
    import backend.RAG.opensearch.schema as schema

    calls: list[tuple] = []

    class FakeTransport:
        def perform_request(self, method, path, body=None):
            calls.append((method, path, body))

    class FakeClient:
        transport = FakeTransport()

    monkeypatch.setattr(schema, "get_opensearch_client", lambda: FakeClient())
    monkeypatch.setattr(schema.settings, "hybrid_pipeline_name", "pipe-x")

    name = schema.ensure_search_pipeline()
    assert name == "pipe-x"
    assert calls[0][0] == "PUT"
    assert calls[0][1] == "/_search/pipeline/pipe-x"


def test_ensure_index_create_and_recreate(monkeypatch):
    import backend.RAG.opensearch.schema as schema

    exists = False
    created: list[tuple] = []
    deleted: list = []

    class FakeIndices:
        def exists(self, index=None):
            return exists

        def delete(self, index=None):
            nonlocal exists
            deleted.append(index)
            exists = False

        def create(self, index=None, body=None):
            nonlocal exists
            created.append((index, body))
            exists = True

    class FakeClient:
        indices = FakeIndices()

    monkeypatch.setattr(schema, "get_opensearch_client", lambda: FakeClient())
    monkeypatch.setattr(schema, "ensure_search_pipeline", lambda: "pipe")
    monkeypatch.setattr(schema.settings, "opensearch_index", "rag-idx")

    name = schema.ensure_index()
    assert name == "rag-idx"
    assert len(created) == 1

    exists = True
    schema.ensure_index(recreate=True)
    assert "rag-idx" in deleted
    assert len(created) == 2
