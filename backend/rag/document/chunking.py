"""文本切分。"""

from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import settings


def split_text_to_chunks(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap or settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""],
        length_function=len,
    )
    return splitter.split_text(text)
