"""document.embed 单元测试（mock HuggingFaceEmbeddings）。"""

from __future__ import annotations


def test_embed_chunks_and_query(monkeypatch):
    import backend.rag.document.embed as embed_mod

    embed_mod._embedding_model = None

    class FakeModel:
        def embed_documents(self, chunks):
            return [[float(i)] for i, _ in enumerate(chunks)]

        def embed_query(self, query):
            return [0.42]

    monkeypatch.setattr(
        embed_mod,
        "HuggingFaceEmbeddings",
        lambda **kwargs: FakeModel(),
    )

    assert embed_mod.embed_chunks(["a", "b"]) == [[0.0], [1.0]]
    assert embed_mod.embed_query("q") == [0.42]
    # singleton
    assert embed_mod.get_embedding_model() is embed_mod.get_embedding_model()
    embed_mod._embedding_model = None


def test_parse_pdf_with_mineru_mocked(tmp_path, monkeypatch):
    import types

    import backend.rag.document.pdf as pdf_mod

    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF")
    out_dir = tmp_path / "mineru_out"
    md_dir = out_dir / "doc" / "auto"
    md_dir.mkdir(parents=True)
    md_path = md_dir / "doc.md"
    md_path.write_text("# ok", encoding="utf-8")

    fake_common = types.SimpleNamespace(
        read_fn=lambda p: b"bytes",
        do_parse=lambda **kwargs: None,
    )

    def fake_import(name):
        if name == "mineru.cli.common":
            return fake_common
        raise ImportError(name)

    monkeypatch.setattr(
        "importlib.import_module",
        lambda name: (
            fake_common
            if name == "mineru.cli.common"
            else (_ for _ in ()).throw(ImportError(name))
        ),
    )

    result = pdf_mod.parse_pdf_with_mineru(str(pdf), output_dir=str(out_dir))
    assert result == str(md_path)


def test_parse_pdf_import_error(monkeypatch):
    import backend.rag.document.pdf as pdf_mod
    import pytest

    monkeypatch.setattr(
        "importlib.import_module",
        lambda name: (_ for _ in ()).throw(ImportError("no mineru")),
    )
    with pytest.raises(ImportError, match="未安装 mineru"):
        pdf_mod.parse_pdf_with_mineru("anything.pdf")
