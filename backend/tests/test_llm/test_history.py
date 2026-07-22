"""LLM session.history 单元测试。"""

from __future__ import annotations

import pytest


def test_get_history_requires_uuid_and_section_id(monkeypatch):
    import backend.llm.session.history as history_mod
    from backend.config import settings

    captured: dict = {}

    class FakeRedisHistory:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(history_mod, "RedisChatMessageHistory", FakeRedisHistory)

    hist = history_mod.get_history("user-9", "sec-42")
    assert isinstance(hist, FakeRedisHistory)
    assert captured["session_id"] == "user-9::sec-42"
    assert captured["redis_url"] == settings.redis_url
    assert captured["ttl"] == settings.redis_history_ttl

    with pytest.raises(ValueError, match="uuid"):
        history_mod.get_history("", "sec-1")
    with pytest.raises(ValueError, match="section_id"):
        history_mod.get_history("u1", "  ")


def test_get_history_by_session_key(monkeypatch):
    import backend.llm.session.history as history_mod

    captured: dict = {}

    class FakeRedisHistory:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(history_mod, "RedisChatMessageHistory", FakeRedisHistory)

    history_mod.get_history_by_session_key("user-9::sec-1")
    assert captured["session_id"] == "user-9::sec-1"

    with pytest.raises(ValueError, match="session_id"):
        history_mod.get_history_by_session_key("only-section")


def test_clear_history(monkeypatch):
    import backend.llm.session.history as history_mod

    cleared: list[str] = []

    class FakeRedisHistory:
        def __init__(self, **kwargs):
            self.session_id = kwargs["session_id"]

        def clear(self) -> None:
            cleared.append(self.session_id)

    monkeypatch.setattr(history_mod, "RedisChatMessageHistory", FakeRedisHistory)
    history_mod.clear_history("u1", "s1")
    assert cleared == ["u1::s1"]


def test_clear_histories_for_uuid(monkeypatch):
    import backend.llm.session.history as history_mod

    cleared: list[str] = []

    class FakeRedisHistory:
        def __init__(self, **kwargs):
            self.session_id = kwargs["session_id"]

        def clear(self) -> None:
            cleared.append(self.session_id)

    monkeypatch.setattr(history_mod, "RedisChatMessageHistory", FakeRedisHistory)
    monkeypatch.setattr(
        history_mod,
        "list_history_session_ids_for_uuid",
        lambda uuid: [f"{uuid}::a", f"{uuid}::b"],
    )
    out = history_mod.clear_histories_for_uuid("user-9")
    assert out == ["user-9::a", "user-9::b"]
    assert cleared == ["user-9::a", "user-9::b"]
