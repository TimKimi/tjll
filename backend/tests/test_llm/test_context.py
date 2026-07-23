"""LLM pipeline.context 单元测试。"""

from langchain_core.documents import Document

from backend.llm.pipeline.context import format_docs


def test_format_docs():
    docs = [
        Document(
            page_content="正文A",
            metadata={"name": "a.txt", "chunk_index": 0},
        ),
        Document(
            page_content="正文B",
            metadata={"id": "doc-2", "chunk_index": 1},
        ),
    ]
    text = format_docs(docs)
    assert "片段 1" in text
    assert "a.txt" in text
    assert "正文A" in text
    assert "片段 2" in text
    assert "正文B" in text
