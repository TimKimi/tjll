"""document.chunking 单元测试。"""

from __future__ import annotations

from backend.RAG.document.chunking import split_text_to_chunks


def test_split_text_to_chunks_with_explicit_size():
    text = "一二三四五六七八九十" * 5
    chunks = split_text_to_chunks(text, chunk_size=20, chunk_overlap=5)
    assert len(chunks) >= 2
    assert all(isinstance(c, str) and c for c in chunks)


def test_split_text_to_chunks_short_text_single_chunk():
    chunks = split_text_to_chunks("短文本", chunk_size=100, chunk_overlap=10)
    assert chunks == ["短文本"]
