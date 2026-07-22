"""document.loaders 单元测试（mock 重依赖）。"""

from __future__ import annotations

from pathlib import Path

import pytest


def test_load_md_file(tmp_path):
    from backend.rag.document.loaders import load_document_as_text

    path = tmp_path / "note.md"
    path.write_text("# 标题\n内容", encoding="utf-8")
    assert "标题" in load_document_as_text(str(path))


def test_load_txt_file(tmp_path, monkeypatch):
    from langchain_core.documents import Document

    path = tmp_path / "a.txt"
    path.write_text("hello txt", encoding="utf-8")

    class FakeTextLoader:
        def __init__(self, *_a, **_k):
            pass

        def load(self):
            return [Document(page_content="hello txt")]

    monkeypatch.setattr(
        "langchain_community.document_loaders.TextLoader",
        FakeTextLoader,
    )
    from backend.rag.document.loaders import load_document_as_text

    assert load_document_as_text(str(path)) == "hello txt"


def test_load_missing_file_raises():
    from backend.rag.document.loaders import load_document_as_text

    with pytest.raises(FileNotFoundError, match="文件不存在"):
        load_document_as_text("D:/no/such/file.md")


def test_load_unsupported_extension(tmp_path):
    from backend.rag.document.loaders import load_document_as_text

    path = tmp_path / "a.bin"
    path.write_bytes(b"x")
    with pytest.raises(ValueError, match="不支持的文件类型"):
        load_document_as_text(str(path))


def test_load_pdf_uses_mineru(tmp_path, monkeypatch):
    import backend.rag.document.loaders as loaders_mod

    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF")
    md = tmp_path / "out.md"
    md.write_text("parsed md", encoding="utf-8")

    monkeypatch.setattr(
        loaders_mod,
        "parse_pdf_with_mineru",
        lambda _p: str(md),
    )
    assert loaders_mod.load_document_as_text(str(pdf)) == "parsed md"


def test_load_docx(tmp_path, monkeypatch):
    from langchain_core.documents import Document

    path = tmp_path / "a.docx"
    path.write_bytes(b"PK")

    class FakeWordLoader:
        def __init__(self, *_a, **_k):
            pass

        def load(self):
            return [
                Document(page_content="段1"),
                Document(page_content="段2"),
            ]

    monkeypatch.setattr(
        "langchain_community.document_loaders.UnstructuredWordDocumentLoader",
        FakeWordLoader,
    )
    from backend.rag.document.loaders import load_document_as_text

    assert load_document_as_text(str(path)) == "段1\n\n段2"


def test_load_excel_openpyxl_fallback(tmp_path, monkeypatch):
    import backend.rag.document.loaders as loaders_mod

    path = tmp_path / "a.xlsx"
    path.write_bytes(b"PK")

    class BadExcelLoader:
        def __init__(self, *_a, **_k):
            raise RuntimeError("unstructured unavailable")

    monkeypatch.setattr(
        "langchain_community.document_loaders.UnstructuredExcelLoader",
        BadExcelLoader,
    )

    class FakeSheet:
        title = "Sheet1"

        def iter_rows(self, values_only=True):
            yield ("A", "B")
            yield (None, None)
            yield ("1", "2")

    class FakeWb:
        worksheets = [FakeSheet()]

        def close(self):
            pass

    import types

    fake_openpyxl = types.ModuleType("openpyxl")
    setattr(fake_openpyxl, "load_workbook", lambda *a, **k: FakeWb())
    monkeypatch.setitem(
        __import__("sys").modules,
        "openpyxl",
        fake_openpyxl,
    )

    text = loaders_mod._load_excel_as_text(Path(path))
    assert "Sheet: Sheet1" in text
    assert "A\tB" in text
    assert "1\t2" in text


def test_file_to_chunks_pipeline(tmp_path, monkeypatch):
    import backend.rag.document.loaders as loaders_mod

    path = tmp_path / "note.md"
    path.write_text("hello\n\nworld", encoding="utf-8")

    monkeypatch.setattr(loaders_mod, "clean_text", lambda t: t.strip())
    monkeypatch.setattr(
        loaders_mod,
        "split_text_to_chunks",
        lambda text, chunk_size=None, chunk_overlap=None: ["hello", "world"],
    )

    assert loaders_mod.file_to_chunks(str(path)) == ["hello", "world"]


def test_file_to_chunks_empty_after_clean(tmp_path, monkeypatch):
    import backend.rag.document.loaders as loaders_mod

    path = tmp_path / "empty.md"
    path.write_text("   ", encoding="utf-8")
    monkeypatch.setattr(loaders_mod, "clean_text", lambda _t: "")

    assert loaders_mod.file_to_chunks(str(path)) == []
