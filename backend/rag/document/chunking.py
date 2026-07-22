"""文本切分。"""

from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import settings

_DEFAULT_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "，", " ", ""]


def split_text_to_chunks(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    *,
    separators: list[str] | None = None,
) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap
        if chunk_overlap is not None
        else settings.chunk_overlap,
        separators=separators if separators is not None else _DEFAULT_SEPARATORS,
        length_function=len,
    )
    return splitter.split_text(text)
