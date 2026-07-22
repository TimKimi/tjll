"""统一文档加载：按后缀返回纯文本 / Markdown；可选切成 chunk（不入库）。"""

from __future__ import annotations

from pathlib import Path

from backend.rag.document.chunking import split_text_to_chunks
from backend.rag.document.clean import clean_text
from backend.rag.document.paths import (
    SUPPORTED_EXTS,
    resolve_repo_path,
)
from backend.rag.document.pdf import parse_pdf_with_mineru

_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}

__all__ = [
    "SUPPORTED_EXTS",
    "file_to_chunks",
    "load_document_as_text",
    "resolve_repo_path",
]


def load_document_as_text(file_path: str) -> str:
    """根据后缀选择 Loader，返回纯文本（PDF/图片经 MinerU 转为 Markdown）。"""
    path = resolve_repo_path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    ext = path.suffix.lower()

    if ext == ".pdf":
        md_path = parse_pdf_with_mineru(str(path))
        return Path(md_path).read_text(encoding="utf-8")

    if ext in _IMAGE_EXTS:
        from backend.rag.document.image import parse_image_with_mineru

        md_path = parse_image_with_mineru(str(path))
        return Path(md_path).read_text(encoding="utf-8")

    if ext == ".md":
        return path.read_text(encoding="utf-8")

    if ext == ".txt":
        from langchain_community.document_loaders import TextLoader

        return TextLoader(str(path), encoding="utf-8").load()[0].page_content

    if ext in (".doc", ".docx"):
        from langchain_community.document_loaders import (
            UnstructuredWordDocumentLoader,
        )

        docs = UnstructuredWordDocumentLoader(str(path)).load()
        return "\n\n".join(doc.page_content for doc in docs)

    raise ValueError(
        f"不支持的文件类型: {ext}。支持: " + " ".join(sorted(SUPPORTED_EXTS))
    )


def file_to_chunks(
    file_path: str,
    *,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[str]:
    """加载文件 → 清洗 → 切分为 chunk 列表（不做 embedding / 入库）。"""
    text = clean_text(load_document_as_text(file_path))
    if not text:
        return []
    return split_text_to_chunks(
        text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
