"""OpenSearch 客户端。"""

from opensearchpy import OpenSearch

from backend.config import settings


def get_opensearch_client() -> OpenSearch:
    return OpenSearch(
        hosts=[
            {
                "host": settings.opensearch_host,
                "port": settings.opensearch_port,
            }
        ],
        http_auth=(settings.opensearch_user, settings.opensearch_password),
        use_ssl=settings.opensearch_use_ssl,
        verify_certs=settings.opensearch_verify_certs,
        ssl_show_warn=False,
    )
