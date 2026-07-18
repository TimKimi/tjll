"""Embedding 单例。"""

from __future__ import annotations

import logging

from langchain_huggingface import HuggingFaceEmbeddings

from backend.config import settings

logger = logging.getLogger(__name__)

_embedding_model: HuggingFaceEmbeddings | None = None


def resolve_embedding_device(requested: str | None = None) -> str:
    """解析 embedding 设备；请求 cuda 但当前 torch 无 CUDA 时回退 cpu。"""
    device = (requested or settings.embedding_device or "cpu").strip().lower()
    if device.startswith("cuda"):
        try:
            import torch

            if not torch.cuda.is_available():
                logger.warning(
                    "EMBEDDING_DEVICE=%s 但当前 Torch 未启用 CUDA，回退到 cpu",
                    device,
                )
                return "cpu"
        except ImportError:
            logger.warning("未安装 torch，EMBEDDING_DEVICE=%s 回退到 cpu", device)
            return "cpu"
    return device


def get_embedding_model() -> HuggingFaceEmbeddings:
    global _embedding_model
    if _embedding_model is None:
        device = resolve_embedding_device()
        _embedding_model = HuggingFaceEmbeddings(
            model_name=settings.embedding_model_dir,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedding_model


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    return get_embedding_model().embed_documents(chunks)


def embed_query(query: str) -> list[float]:
    return get_embedding_model().embed_query(query)
