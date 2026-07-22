"""索引入库：Yelp cleaned chunks / 用户洞察 → Embedding → OpenSearch bulk。"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Literal

from opensearchpy.helpers import bulk

from backend.config import settings
from backend.rag.document.chunking import split_text_to_chunks
from backend.rag.document.clean import clean_text, normalize_jsonish
from backend.rag.document.embed import embed_chunks
from backend.rag.opensearch.client import get_opensearch_client
from backend.rag.opensearch.schema import (
    ensure_index,
    ensure_insight_index,
    ensure_section_document_index,
    ensure_section_insight_index,
)

logger = logging.getLogger("backend.rag.document.indexing")

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
    now = datetime.now(timezone.utc).isoformat()
    last_idx = len(chunks) - 1
    docs: list[dict[str, Any]] = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
        doc: dict[str, Any] = {
            **business,
            "chunk_id": make_chunk_id(business_id, polarity, idx),
            "polarity": polarity,
            "chunk_index": idx,
            "is_last_chunk": idx == last_idx,
            "text": chunk,
            "embedding": embedding,
            "created_at": now,
        }
        docs.append(doc)
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
    logger.info(
        "index business_id=%s name=%s index=%s",
        business_id,
        business.get("name"),
        index_name or settings.opensearch_index,
    )

    pos_docs = _chunks_for_polarity(raw, business, "positive", "positive_summary")
    neg_docs = _chunks_for_polarity(raw, business, "negative", "negative_summary")

    if not pos_docs and not neg_docs:
        return {
            "id": business_id,
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
                "id": business_id,
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
                "id": business_id,
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
        "id": business_id,
        "chunks": len(pos_docs) + len(neg_docs),
        "dims": dims,
        "success": total_success,
        "errors": all_errors,
        "positive_chunks": len(pos_docs),
        "negative_chunks": len(neg_docs),
        "both_sides_complete": both,
    }


def make_insight_chunk_id(uuid: str, chunk_index: int) -> str:
    """洞察 chunk_id：``{uuid}_{index}``。"""
    return f"{uuid}_{chunk_index}"


def build_insight_chunk_docs(
    uuid: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    docs: list[dict[str, Any]] = []
    for i, (text, emb) in enumerate(zip(chunks, embeddings, strict=True)):
        docs.append(
            {
                "chunk_id": make_insight_chunk_id(uuid, i),
                "document_id": uuid,
                "chunk_index": i,
                "text": text,
                "embedding": emb,
                "created_at": now,
            }
        )
    return docs


def index_insight_chunks(
    uuid: str,
    chunks: list[str],
    *,
    index_name: str | None = None,
    ensure: bool = True,
) -> tuple[int, list]:
    """Embed + bulk 写入用户洞察索引。"""
    if not chunks:
        return 0, []
    index_name = index_name or settings.opensearch_insight_index
    if ensure:
        ensure_insight_index(index_name)
    embeddings = embed_chunks(chunks)
    docs = build_insight_chunk_docs(uuid, chunks, embeddings)
    success, errors = index_chunks_to_opensearch(docs, index_name=index_name)
    logger.info(
        "index_insight_chunks uuid=%s chunks=%d success=%s",
        uuid,
        len(chunks),
        success,
    )
    return success, errors


def delete_insight_from_opensearch(
    uuid: str,
    *,
    index_name: str | None = None,
) -> int:
    """按 uuid（document_id）删除洞察索引中的全部 chunk；返回删除条数。"""
    uuid = (uuid or "").strip()
    if not uuid:
        raise ValueError("uuid is required")
    client = get_opensearch_client()
    index_name = index_name or settings.opensearch_insight_index
    if not client.indices.exists(index=index_name):
        logger.info("delete_insight skip missing index=%s uuid=%s", index_name, uuid)
        return 0
    resp = client.delete_by_query(
        index=index_name,
        body={"query": {"term": {"document_id": uuid}}},
        refresh=True,
        conflicts="proceed",
    )
    deleted = int(resp.get("deleted") or 0)
    logger.info(
        "delete_insight_from_opensearch uuid=%s deleted=%d",
        uuid,
        deleted,
    )
    return deleted


def make_section_insight_chunk_id(uuid: str, section_id: str, chunk_index: int) -> str:
    """会话属性 chunk_id：``{uuid}_{section_id}_{index}``。"""
    return f"{uuid}_{section_id}_{chunk_index}"


def make_section_document_chunk_id(
    uuid: str,
    section_id: str,
    source_file: str,
    chunk_index: int,
) -> str:
    """文档 chunk_id：``{sha1(uuid|section_id|source_file)[:16]}_{chunk_index:04d}``。"""
    digest = hashlib.sha1(
        f"{uuid}|{section_id}|{source_file}".encode("utf-8")
    ).hexdigest()[:16]
    return f"{digest}_{chunk_index:04d}"


def build_section_insight_chunk_docs(
    uuid: str,
    section_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    docs: list[dict[str, Any]] = []
    for i, (text, emb) in enumerate(zip(chunks, embeddings, strict=True)):
        docs.append(
            {
                "chunk_id": make_section_insight_chunk_id(uuid, section_id, i),
                "document_id": uuid,
                "section_id": section_id,
                "chunk_index": i,
                "text": text,
                "embedding": emb,
                "created_at": now,
            }
        )
    return docs


def build_section_document_chunk_docs(
    uuid: str,
    section_id: str,
    source_file: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    docs: list[dict[str, Any]] = []
    for i, (text, emb) in enumerate(zip(chunks, embeddings, strict=True)):
        docs.append(
            {
                "chunk_id": make_section_document_chunk_id(
                    uuid, section_id, source_file, i
                ),
                "document_id": uuid,
                "section_id": section_id,
                "source_file": source_file,
                "chunk_index": i,
                "text": text,
                "embedding": emb,
                "created_at": now,
            }
        )
    return docs


def index_section_insight_chunks(
    uuid: str,
    section_id: str,
    chunks: list[str],
    *,
    index_name: str | None = None,
    ensure: bool = True,
) -> tuple[int, list]:
    """Embed + bulk 写入会话洞察属性索引。"""
    if not chunks:
        return 0, []
    index_name = index_name or settings.opensearch_section_insight_index
    if ensure:
        ensure_section_insight_index(index_name)
    embeddings = embed_chunks(chunks)
    docs = build_section_insight_chunk_docs(uuid, section_id, chunks, embeddings)
    success, errors = index_chunks_to_opensearch(docs, index_name=index_name)
    logger.info(
        "index_section_insight_chunks uuid=%s section_id=%s chunks=%d success=%s",
        uuid,
        section_id,
        len(chunks),
        success,
    )
    return success, errors


def delete_section_insight_from_opensearch(
    uuid: str,
    section_id: str,
    *,
    index_name: str | None = None,
) -> int:
    """按 uuid + section_id 删除会话属性切块。"""
    uuid = (uuid or "").strip()
    section_id = (section_id or "").strip()
    if not uuid or not section_id:
        raise ValueError("uuid and section_id are required")
    client = get_opensearch_client()
    index_name = index_name or settings.opensearch_section_insight_index
    if not client.indices.exists(index=index_name):
        return 0
    resp = client.delete_by_query(
        index=index_name,
        body={
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"document_id": uuid}},
                        {"term": {"section_id": section_id}},
                    ]
                }
            }
        },
        refresh=True,
        conflicts="proceed",
    )
    deleted = int(resp.get("deleted") or 0)
    logger.info(
        "delete_section_insight uuid=%s section_id=%s deleted=%d",
        uuid,
        section_id,
        deleted,
    )
    return deleted


def index_section_document_chunks(
    uuid: str,
    section_id: str,
    source_file: str,
    chunks: list[str],
    *,
    index_name: str | None = None,
    ensure: bool = True,
) -> tuple[int, list]:
    """覆盖写入单个上传文件的切块（先删同 source_file 再 bulk）。"""
    source_file = (source_file or "").strip()
    if not source_file:
        raise ValueError("source_file is required")
    index_name = index_name or settings.opensearch_section_document_index
    if ensure:
        ensure_section_document_index(index_name)
    delete_section_document_from_opensearch(
        uuid,
        section_id,
        source_file=source_file,
        index_name=index_name,
    )
    if not chunks:
        return 0, []
    embeddings = embed_chunks(chunks)
    docs = build_section_document_chunk_docs(
        uuid, section_id, source_file, chunks, embeddings
    )
    success, errors = index_chunks_to_opensearch(docs, index_name=index_name)
    logger.info(
        "index_section_document_chunks uuid=%s section_id=%s file=%s chunks=%d",
        uuid,
        section_id,
        source_file,
        len(chunks),
    )
    return success, errors


def delete_section_document_from_opensearch(
    uuid: str,
    section_id: str,
    *,
    source_file: str | None = None,
    index_name: str | None = None,
) -> int:
    """按 uuid+section_id（可选 source_file）删除文档切块。"""
    uuid = (uuid or "").strip()
    section_id = (section_id or "").strip()
    if not uuid or not section_id:
        raise ValueError("uuid and section_id are required")
    client = get_opensearch_client()
    index_name = index_name or settings.opensearch_section_document_index
    if not client.indices.exists(index=index_name):
        return 0
    filters: list[dict[str, Any]] = [
        {"term": {"document_id": uuid}},
        {"term": {"section_id": section_id}},
    ]
    if source_file:
        filters.append({"term": {"source_file": source_file.strip()}})
    resp = client.delete_by_query(
        index=index_name,
        body={"query": {"bool": {"filter": filters}}},
        refresh=True,
        conflicts="proceed",
    )
    deleted = int(resp.get("deleted") or 0)
    logger.info(
        "delete_section_document uuid=%s section_id=%s file=%s deleted=%d",
        uuid,
        section_id,
        source_file,
        deleted,
    )
    return deleted
