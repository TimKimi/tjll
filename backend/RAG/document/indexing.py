"""索引入库：加载 → 清洗 → 切分 → Embedding → OpenSearch bulk。"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from opensearchpy.helpers import bulk

from backend.RAG.document.chunking import split_text_to_chunks
from backend.RAG.document.clean import clean_text
from backend.RAG.document.embed import embed_chunks
from backend.RAG.document.loaders import load_document_as_text
from backend.RAG.opensearch.client import get_opensearch_client
from backend.RAG.opensearch.schema import ensure_index
from backend.config import settings


def make_document_id(file_path: str) -> str:
    return hashlib.md5(file_path.encode("utf-8")).hexdigest()[:12]


def build_chunk_docs(
    file_path: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> list[dict]:
    document_id = make_document_id(file_path)
    source_file = Path(file_path).name
    now = datetime.now(timezone.utc).isoformat()
    docs: list[dict] = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
        chunk_id = f"{document_id}_chunk_{idx:04d}"
        docs.append(
            {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "source_file": source_file,
                "chunk_index": idx,
                "text": chunk,
                "embedding": embedding,
                "created_at": now,
            }
        )
    return docs


def index_chunks_to_opensearch(
    docs: list[dict],
    index_name: str | None = None,
) -> tuple[int, list]:
    client = get_opensearch_client()
    index_name = index_name or settings.opensearch_index
    actions = [
        {
            "_op_type": "index",
            "_index": index_name,
            "_id": doc["chunk_id"],
            "_source": doc,
        }
        for doc in docs
    ]
    success, errors = bulk(client, actions, chunk_size=100)
    client.indices.refresh(index=index_name)
    return success, errors


def index_file_to_opensearch(
    file_path: str,
    *,
    index_name: str | None = None,
    ensure: bool = True,
) -> dict:
    """端到端：读文件 → 清洗 → 切分 → 向量化 → 写入 OpenSearch。"""
    if ensure:
        ensure_index(index_name)

    text = clean_text(load_document_as_text(file_path))
    if not text:
        return {"chunks": 0, "success": 0, "errors": []}

    chunks = split_text_to_chunks(text)
    embeddings = embed_chunks(chunks)
    docs = build_chunk_docs(file_path, chunks, embeddings)
    success, errors = index_chunks_to_opensearch(docs, index_name=index_name)
    return {
        "document_id": make_document_id(file_path),
        "chunks": len(chunks),
        "dims": len(embeddings[0]) if embeddings else 0,
        "success": success,
        "errors": errors,
    }
