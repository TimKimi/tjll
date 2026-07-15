"""Embedding 单例。"""

from __future__ import annotations

from langchain_huggingface import HuggingFaceEmbeddings

from backend.config import settings

_embedding_model: HuggingFaceEmbeddings | None = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = HuggingFaceEmbeddings(
            model_name=settings.embedding_model_dir,
            model_kwargs={"device": settings.embedding_device},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedding_model


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    return get_embedding_model().embed_documents(chunks)


def embed_query(query: str) -> list[float]:
    return get_embedding_model().embed_query(query)
