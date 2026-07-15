"""OpenSearch 包。"""

from backend.RAG.opensearch.client import get_opensearch_client
from backend.RAG.opensearch.schema import ensure_index, ensure_search_pipeline

__all__ = ["get_opensearch_client", "ensure_index", "ensure_search_pipeline"]
