"""OpenSearch 包。"""

from backend.rag.opensearch.client import get_opensearch_client
from backend.rag.opensearch.schema import ensure_index, ensure_search_pipeline

__all__ = ["get_opensearch_client", "ensure_index", "ensure_search_pipeline"]
