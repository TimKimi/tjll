"""section 文档索引 chunk_id / mapping 单元测试。"""

from __future__ import annotations

import hashlib


def test_make_section_document_chunk_id_stable():
    from backend.rag.document.indexing import make_section_document_chunk_id

    a = make_section_document_chunk_id("u", "s", "a.md", 0)
    b = make_section_document_chunk_id("u", "s", "a.md", 0)
    c = make_section_document_chunk_id("u", "s", "a.md", 1)
    digest = hashlib.sha1(b"u|s|a.md").hexdigest()[:16]
    assert a == b == f"{digest}_0000"
    assert c == f"{digest}_0001"


def test_section_insight_mapping_has_section_id():
    from backend.rag.opensearch.schema import (
        section_document_index_mapping_body,
        section_insight_index_mapping_body,
    )

    props = section_insight_index_mapping_body(dims=8)["mappings"]["properties"]
    assert "section_id" in props
    assert "document_id" in props

    doc_props = section_document_index_mapping_body(dims=8)["mappings"]["properties"]
    assert "source_file" in doc_props
    assert "section_id" in doc_props


def test_build_section_document_chunk_docs():
    from backend.rag.document.indexing import build_section_document_chunk_docs

    docs = build_section_document_chunk_docs(
        "u1",
        "sec1",
        "docs/a.md",
        chunks=["t0", "t1"],
        embeddings=[[0.1], [0.2]],
    )
    assert len(docs) == 2
    assert docs[0]["document_id"] == "u1"
    assert docs[0]["section_id"] == "sec1"
    assert docs[0]["source_file"] == "docs/a.md"
    assert docs[0]["chunk_index"] == 0
    assert docs[1]["chunk_index"] == 1
