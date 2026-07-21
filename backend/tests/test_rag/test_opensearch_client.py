"""opensearch.client 单元测试。"""

from __future__ import annotations


def test_get_opensearch_client_uses_settings(monkeypatch):
    import backend.rag.opensearch.client as client_mod
    from backend.config import settings

    captured: dict = {}

    class FakeOpenSearch:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(client_mod, "OpenSearch", FakeOpenSearch)

    client = client_mod.get_opensearch_client()
    assert isinstance(client, FakeOpenSearch)
    assert captured["hosts"] == [
        {"host": settings.opensearch_host, "port": settings.opensearch_port}
    ]
    assert captured["http_auth"] == (
        settings.opensearch_user,
        settings.opensearch_password,
    )
    assert captured["use_ssl"] == settings.opensearch_use_ssl
    assert captured["verify_certs"] == settings.opensearch_verify_certs
    assert captured["ssl_show_warn"] is False
