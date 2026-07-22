"""索引 mapping 与 hybrid Search Pipeline（yelp_biz_v1 / user_insight_v1）。"""

from __future__ import annotations

import logging
from typing import Any

from backend.config import settings
from backend.rag.opensearch.client import get_opensearch_client

logger = logging.getLogger("backend.rag.opensearch.schema")


def _keyword() -> dict:
    return {"type": "keyword"}


def _keyword_with_text() -> dict:
    return {
        "type": "keyword",
        "fields": {
            "text": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart",
            }
        },
    }


def index_mapping_body(dims: int | None = None) -> dict:
    dims = dims or settings.embedding_dims
    return {
        "settings": {
            "index": {
                "knn": True,
                "number_of_shards": 1,
                "number_of_replicas": 0,
            },
            "analysis": {
                "analyzer": {
                    "ik_smart_analyzer": {"type": "ik_smart"},
                    "ik_max_analyzer": {"type": "ik_max_word"},
                }
            },
        },
        "mappings": {
            "properties": {
                # business fields
                "id": _keyword(),
                "alias": _keyword_with_text(),
                "name": _keyword_with_text(),
                "image_url": _keyword(),
                "is_closed": {"type": "boolean"},
                "url": _keyword(),
                "review_count": {"type": "integer"},
                "rating": {"type": "float"},
                "price": _keyword(),
                "categories": _keyword_with_text(),
                "latitude": {"type": "float"},
                "longitude": {"type": "float"},
                "address": _keyword_with_text(),
                "phone": _keyword(),
                "display_phone": _keyword(),
                "hours": _keyword(),
                "transactions": _keyword(),
                "photos": _keyword(),
                "yelp_menu_url": _keyword(),
                # chunk fields
                "chunk_id": _keyword(),
                "polarity": _keyword(),
                "chunk_index": {"type": "integer"},
                "is_last_chunk": {"type": "boolean"},
                "text": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart",
                },
                "embedding": {
                    "type": "knn_vector",
                    "dimension": dims,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib",
                        "parameters": {"ef_construction": 128, "m": 16},
                    },
                },
                "created_at": {"type": "date"},
            }
        },
    }


def insight_index_mapping_body(dims: int | None = None) -> dict[str, Any]:
    """用户洞察索引 mapping（精简：chunk_id / document_id / text / embedding）。"""
    dims = dims or settings.embedding_dims
    return {
        "settings": {
            "index": {
                "knn": True,
                "number_of_shards": 1,
                "number_of_replicas": 0,
            },
            "analysis": {
                "analyzer": {
                    "ik_smart_analyzer": {"type": "ik_smart"},
                    "ik_max_analyzer": {"type": "ik_max_word"},
                }
            },
        },
        "mappings": {
            "properties": {
                "chunk_id": _keyword(),
                "document_id": _keyword(),
                "chunk_index": {"type": "integer"},
                "text": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart",
                },
                "embedding": {
                    "type": "knn_vector",
                    "dimension": dims,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib",
                        "parameters": {"ef_construction": 128, "m": 16},
                    },
                },
                "created_at": {"type": "date"},
            }
        },
    }


def section_insight_index_mapping_body(dims: int | None = None) -> dict[str, Any]:
    """会话洞察属性索引：用户洞察字段 + section_id。"""
    body = insight_index_mapping_body(dims)
    body["mappings"]["properties"]["section_id"] = _keyword()
    return body


def section_document_index_mapping_body(dims: int | None = None) -> dict[str, Any]:
    """会话上传文档切块索引。"""
    dims = dims or settings.embedding_dims
    return {
        "settings": {
            "index": {
                "knn": True,
                "number_of_shards": 1,
                "number_of_replicas": 0,
            },
            "analysis": {
                "analyzer": {
                    "ik_smart_analyzer": {"type": "ik_smart"},
                    "ik_max_analyzer": {"type": "ik_max_word"},
                }
            },
        },
        "mappings": {
            "properties": {
                "chunk_id": _keyword(),
                "document_id": _keyword(),
                "section_id": _keyword(),
                "source_file": _keyword(),
                "chunk_index": {"type": "integer"},
                "text": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart",
                },
                "embedding": {
                    "type": "knn_vector",
                    "dimension": dims,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib",
                        "parameters": {"ef_construction": 128, "m": 16},
                    },
                },
                "created_at": {"type": "date"},
            }
        },
    }


def hybrid_pipeline_body() -> dict:
    """normalization-processor：配合 hybrid query 做分数归一化与加权融合。"""
    return {
        "description": "Hybrid search score normalization for RAG",
        "phase_results_processors": [
            {
                "normalization-processor": {
                    "normalization": {"technique": "min_max"},
                    "combination": {
                        "technique": "arithmetic_mean",
                        "parameters": {
                            "weights": [
                                settings.hybrid_bm25_weight,
                                settings.hybrid_vector_weight,
                            ]
                        },
                    },
                }
            }
        ],
    }


def ensure_search_pipeline(pipeline_name: str | None = None) -> str:
    client = get_opensearch_client()
    name = pipeline_name or settings.hybrid_pipeline_name
    client.transport.perform_request(
        "PUT",
        f"/_search/pipeline/{name}",
        body=hybrid_pipeline_body(),
    )
    return name


def ensure_index(
    index_name: str | None = None,
    *,
    recreate: bool = False,
) -> str:
    """创建索引（含 IK + knn）；可选一并注册 hybrid Search Pipeline。"""
    client = get_opensearch_client()
    index_name = index_name or settings.opensearch_index

    if recreate and client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)

    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name, body=index_mapping_body())

    ensure_search_pipeline()
    return index_name


def ensure_insight_index(
    index_name: str | None = None,
    *,
    recreate: bool = False,
) -> str:
    """创建用户洞察索引（含 IK + knn），并确保 hybrid pipeline 存在。"""
    client = get_opensearch_client()
    index_name = index_name or settings.opensearch_insight_index

    if recreate and client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)

    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name, body=insight_index_mapping_body())
        logger.info("insight index created name=%s", index_name)

    ensure_search_pipeline()
    return index_name


def ensure_section_insight_index(
    index_name: str | None = None,
    *,
    recreate: bool = False,
) -> str:
    """创建会话洞察属性索引。"""
    client = get_opensearch_client()
    index_name = index_name or settings.opensearch_section_insight_index

    if recreate and client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)

    if not client.indices.exists(index=index_name):
        client.indices.create(
            index=index_name,
            body=section_insight_index_mapping_body(),
        )
        logger.info("section insight index created name=%s", index_name)

    ensure_search_pipeline()
    return index_name


def ensure_section_document_index(
    index_name: str | None = None,
    *,
    recreate: bool = False,
) -> str:
    """创建会话上传文档切块索引。"""
    client = get_opensearch_client()
    index_name = index_name or settings.opensearch_section_document_index

    if recreate and client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)

    if not client.indices.exists(index=index_name):
        client.indices.create(
            index=index_name,
            body=section_document_index_mapping_body(),
        )
        logger.info("section document index created name=%s", index_name)

    ensure_search_pipeline()
    return index_name
