"""索引入库：Yelp cleaned chunks / 通用文件 → Embedding → OpenSearch bulk。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from opensearchpy.helpers import bulk

from backend.config import settings
from backend.rag.document.chunking import split_text_to_chunks
from backend.rag.document.clean import clean_text, normalize_jsonish
from backend.rag.document.embed import embed_chunks
from backend.rag.document.loaders import load_document_as_text
from backend.rag.opensearch.client import get_opensearch_client
from backend.rag.opensearch.schema import ensure_index

Polarity = Literal["positive", "negative"]

_POLARITY_TAG: dict[Polarity, str] = {
    "positive": "pos",
    "negative": "neg",
}

_BUSINESS_KEYWORD_FIELDS = (
    "image_url",
    "url",
    "price",
    "phone",
    "display_phone",
    "transactions",
    "photos",
    "yelp_menu_url",
)


def make_document_id(business_id: str) -> str:
    """商家 document_id：直接使用 business id（确定性）。"""
    return business_id


def make_chunk_id(business_id: str, polarity: Polarity, chunk_index: int) -> str:
    """确定性 chunk_id：{business_id}_pos_0000 / {business_id}_neg_0000。"""
    tag = _POLARITY_TAG[polarity]
    return f"{business_id}_{tag}_{chunk_index:04d}"


def normalize_business_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """从 cleaned JSON 提取商家字段并清洗 categories/address/hours。"""
    out: dict[str, Any] = {
        "id": raw.get("id"),
        "alias": raw.get("alias") or "",
        "name": raw.get("name") or "",
        "is_closed": bool(raw.get("is_closed", False)),
        "review_count": int(raw.get("review_count") or 0),
        "rating": float(raw.get("rating") or 0.0),
        "categories": normalize_jsonish(raw.get("categories")),
        "address": normalize_jsonish(raw.get("address")),
        "hours": normalize_jsonish(raw.get("hours")),
    }
    lat = raw.get("latitude")
    lon = raw.get("longitude")
    out["latitude"] = float(lat) if lat is not None else None
    out["longitude"] = float(lon) if lon is not None else None

    for key in _BUSINESS_KEYWORD_FIELDS:
        val = raw.get(key)
        if val is None:
            out[key] = None
        elif isinstance(val, (dict, list)):
            out[key] = normalize_jsonish(val)
        else:
            out[key] = str(val) if val != "" else val
    return out


def build_yelp_chunk_docs(
    business: dict[str, Any],
    polarity: Polarity,
    chunks: list[str],
    embeddings: list[list[float]],
) -> list[dict[str, Any]]:
    """为某一 polarity 的切分结果构建 OpenSearch 文档。"""
    if not chunks:
        return []
    business_id = str(business["id"])
    document_id = make_document_id(business_id)
    now = datetime.now(timezone.utc).isoformat()
    last_idx = len(chunks) - 1
    docs: list[dict[str, Any]] = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
        doc: dict[str, Any] = {
            **business,
            "chunk_id": make_chunk_id(business_id, polarity, idx),
            "document_id": document_id,
            "polarity": polarity,
            "chunk_index": idx,
            "is_last_chunk": idx == last_idx,
            "text": chunk,
            "embedding": embedding,
            "created_at": now,
        }
        docs.append(doc)
    return docs


def build_chunk_docs(
    file_path: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> list[dict]:
    """通用文件入库文档（遗留 PDF/MD 路径）；补齐 mapping 必填默认。"""
    path = Path(file_path)
    document_id = make_document_id(path.stem)
    source_file = path.name
    now = datetime.now(timezone.utc).isoformat()
    last_idx = len(chunks) - 1
    docs: list[dict] = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
        docs.append(
            {
                "id": document_id,
                "alias": "",
                "name": source_file,
                "document_id": document_id,
                "source_file": source_file,
                "chunk_id": make_chunk_id(document_id, "positive", idx),
                "polarity": "positive",
                "chunk_index": idx,
                "is_last_chunk": idx == last_idx,
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


def _chunks_for_polarity(
    raw: dict[str, Any],
    business: dict[str, Any],
    polarity: Polarity,
    field: str,
) -> list[dict[str, Any]]:
    summary = clean_text(str(raw.get(field) or ""))
    if not summary:
        return []
    chunks = split_text_to_chunks(summary)
    if not chunks:
        return []
    embeddings = embed_chunks(chunks)
    return build_yelp_chunk_docs(business, polarity, chunks, embeddings)


def index_business_summaries_to_opensearch(
    raw: dict[str, Any],
    *,
    index_name: str | None = None,
    ensure: bool = False,
) -> dict[str, Any]:
    """单商家：好评/坏评分开切分 → 分别 embed/bulk。

    两侧分两次 bulk：任一侧失败则返回 errors，调用方不得记进度。
    """
    if ensure:
        ensure_index(index_name)

    business = normalize_business_fields(raw)
    business_id = str(business["id"])

    pos_docs = _chunks_for_polarity(raw, business, "positive", "positive_summary")
    neg_docs = _chunks_for_polarity(raw, business, "negative", "negative_summary")

    if not pos_docs and not neg_docs:
        return {
            "document_id": business_id,
            "chunks": 0,
            "success": 0,
            "errors": [],
            "positive_chunks": 0,
            "negative_chunks": 0,
            "both_sides_complete": False,
        }

    total_success = 0
    all_errors: list = []
    dims = 0

    # 好评先写；失败则不写坏评，避免误记完整
    if pos_docs:
        success, errors = index_chunks_to_opensearch(pos_docs, index_name=index_name)
        total_success += success
        if errors:
            all_errors.extend(errors if isinstance(errors, list) else [errors])
            return {
                "document_id": business_id,
                "chunks": len(pos_docs) + len(neg_docs),
                "dims": len(pos_docs[0]["embedding"]),
                "success": total_success,
                "errors": all_errors,
                "positive_chunks": len(pos_docs),
                "negative_chunks": 0,
                "both_sides_complete": False,
            }
        dims = len(pos_docs[0]["embedding"])

    if neg_docs:
        success, errors = index_chunks_to_opensearch(neg_docs, index_name=index_name)
        total_success += success
        if errors:
            all_errors.extend(errors if isinstance(errors, list) else [errors])
            return {
                "document_id": business_id,
                "chunks": len(pos_docs) + len(neg_docs),
                "dims": dims or len(neg_docs[0]["embedding"]),
                "success": total_success,
                "errors": all_errors,
                "positive_chunks": len(pos_docs),
                "negative_chunks": len(neg_docs),
                "both_sides_complete": False,
            }
        dims = dims or len(neg_docs[0]["embedding"])

    both = len(pos_docs) > 0 and len(neg_docs) > 0 and not all_errors
    return {
        "document_id": business_id,
        "chunks": len(pos_docs) + len(neg_docs),
        "dims": dims,
        "success": total_success,
        "errors": all_errors,
        "positive_chunks": len(pos_docs),
        "negative_chunks": len(neg_docs),
        "both_sides_complete": both,
    }


def index_file_to_opensearch(
    file_path: str,
    *,
    index_name: str | None = None,
    ensure: bool = True,
) -> dict:
    """端到端：读完整路径文件 → 清洗 → 切分 → 向量化 → 写入 OpenSearch。"""
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
        "document_id": make_document_id(Path(file_path).stem),
        "chunks": len(chunks),
        "dims": len(embeddings[0]) if embeddings else 0,
        "success": success,
        "errors": errors,
    }
