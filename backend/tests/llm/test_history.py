"""LLM session.history 单元测试。"""

from __future__ import annotations


def test_get_history_passes_redis_config(monkeypatch):
    import backend.LLM.session.history as history_mod
    from backend.config import settings

    captured: dict = {}

    class FakeRedisHistory:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(history_mod, "RedisChatMessageHistory", FakeRedisHistory)

    hist = history_mod.get_history("sec-42")
    assert isinstance(hist, FakeRedisHistory)
    assert captured["session_id"] == "sec-42"
    assert captured["redis_url"] == settings.redis_url
    assert captured["ttl"] == settings.redis_history_ttl
