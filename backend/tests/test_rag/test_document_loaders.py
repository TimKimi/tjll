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


def test_load_image_uses_mineru(tmp_path, monkeypatch):
    import backend.rag.document.loaders as loaders_mod

    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG")
    md = tmp_path / "out.md"
    md.write_text("image md", encoding="utf-8")

    monkeypatch.setattr(
        "backend.rag.document.image.parse_image_with_mineru",
        lambda _p, output_dir=None: str(md),
    )
    monkeypatch.setattr(loaders_mod, "resolve_repo_path", lambda p: img)
    assert loaders_mod.load_document_as_text(str(img)) == "image md"


def test_image_to_single_page_pdf(tmp_path):
    from PIL import Image

    from backend.rag.document.image import image_to_single_page_pdf

    img = tmp_path / "a.png"
    Image.new("RGB", (8, 8), color=(255, 0, 0)).save(img)
    pdf = tmp_path / "a.pdf"
    out = image_to_single_page_pdf(str(img), str(pdf))
    assert Path(out).is_file()
    assert Path(out).stat().st_size > 0
