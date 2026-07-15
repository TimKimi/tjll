"""索引 mapping 与 hybrid Search Pipeline。"""

from __future__ import annotations

from backend.RAG.opensearch.client import get_opensearch_client
from backend.config import settings


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
                "chunk_id": {"type": "keyword"},
                "document_id": {"type": "keyword"},
                "source_file": {"type": "keyword"},
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
