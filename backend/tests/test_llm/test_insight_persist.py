"""洞察 Redis 持久化 / load_section_document / ask used 标记。"""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver

from backend.llm.graph.builder import reset_ask_graph_cache
from backend.llm.graph.session_pool import AskSessionPool, get_session_pool
from backend.llm.insight.registry import (
    drop_section_insight,
    ensure_section_insight,
    get_insight_registry,
)
from backend.llm.insight.section import SectionInsight
from backend.llm.schemas import AskResponse


class _FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.data[key] = value

    def get(self, key: str) -> str | None:
        return self.data.get(key)

    def close(self) -> None:
        return None


class _FakeHistory:
    def __init__(self, messages: list | None = None):
        self.messages = list(messages or [])
        self.added: list = []

    def add_message(self, message) -> None:
        self.added.append(message)
        self.messages.append(message)


def _fake_llm(content: str = "答"):
    class _FakeStreamLLM:
        def stream(self, _messages, config=None, **kwargs):
            yield AIMessage(content=content)

    return _FakeStreamLLM()


def test_user_section_redis_roundtrip(monkeypatch):
    import backend.llm.insight.store as store_mod
    from backend.llm.insight.model import UserInsight

    fake = _FakeRedis()
    monkeypatch.setattr(store_mod, "_client", lambda: fake)

    user = UserInsight("u1")
    user.batch_add({"喜欢": "火锅"})
    user.save_to_redis()
    loaded_user = UserInsight.load_from_redis("u1")
    assert loaded_user is not None
    assert loaded_user.as_dict()["喜欢"] == "火锅"

    section = SectionInsight("u1", "s1", parent=loaded_user)
    section.batch_add_section({"预算": "200"})
    section._filenames = ["docs/a.md"]
    section._used_filenames = ["docs/a.md"]
    section.add_facts(items=["f1"])
    section.set_review("rv")
    section.save_to_redis()

    loaded_sec = SectionInsight.load_section_from_redis("u1", "s1", parent=loaded_user)
    assert loaded_sec is not None
    assert loaded_sec.section_as_dict()["预算"] == "200"
    assert loaded_sec.filenames() == ["docs/a.md"]
    assert loaded_sec.used_filenames() == ["docs/a.md"]
    assert loaded_sec.get_facts() == ["f1"]
    assert loaded_sec.get_review() == "rv"


def test_registry_restore_and_drop_user_when_last_section(monkeypatch):
    import backend.llm.insight.store as store_mod

    fake = _FakeRedis()
    monkeypatch.setattr(store_mod, "_client", lambda: fake)
    get_insight_registry().reset()

    s1 = ensure_section_insight("u-reg", "a")
    s1.batch_add({"k": "v"})
    s2 = ensure_section_insight("u-reg", "b")
    assert s2.as_dict()["k"] == "v"
    assert get_insight_registry().peek_user_insight("u-reg") is not None

    drop_section_insight("u-reg", "a")
    assert get_insight_registry().peek_user_insight("u-reg") is not None
    drop_section_insight("u-reg", "b")
    assert get_insight_registry().peek_user_insight("u-reg") is None


def test_load_section_document_calls_load_file_and_deletes(tmp_path, monkeypatch):
    import backend.llm.graph.service as svc
    import backend.llm.insight.section as sec_mod
    import backend.llm.insight.store as store_mod

    fake = _FakeRedis()
    monkeypatch.setattr(store_mod, "_client", lambda: fake)
    get_insight_registry().reset()

    f = tmp_path / "note.md"
    f.write_text("hello", encoding="utf-8")

    monkeypatch.setattr(sec_mod, "resolve_repo_path", lambda p: f)
    monkeypatch.setattr(sec_mod, "to_repo_relative_posix", lambda p: "note.md")
    monkeypatch.setattr(sec_mod, "load_document_as_text", lambda p: "hello")
    monkeypatch.setattr(sec_mod, "clean_text", lambda t: t)
    monkeypatch.setattr(
        sec_mod,
        "split_text_to_chunks",
        lambda text, chunk_size=None, chunk_overlap=None: ["hello"],
    )
    monkeypatch.setattr(
        sec_mod,
        "index_section_document_chunks",
        lambda *a, **k: (1, []),
    )

    out = svc.load_section_document(
        {"uuid": "u1", "section_id": "s1", "file_path": str(f)}
    )
    assert out.chunks == 1
    assert out.source_file == "note.md"
    assert "note.md" in out.filenames
    assert not f.exists()
    section = ensure_section_insight("u1", "s1")
    assert "note.md" in section.filenames()
    assert section.used_filenames() == []


def test_ask_marks_used_without_load_file(monkeypatch):
    import backend.llm.graph.builder as builder_mod
    import backend.llm.graph.nodes as nodes_mod
    import backend.llm.graph.service as svc
    import backend.llm.graph.session_pool as pool_mod
    import backend.llm.insight.store as store_mod

    fake = _FakeRedis()
    monkeypatch.setattr(store_mod, "_client", lambda: fake)
    get_insight_registry().reset()
    reset_ask_graph_cache()

    redis_hist = _FakeHistory()
    monkeypatch.setattr(pool_mod, "get_history", lambda uuid, section_id: redis_hist)
    monkeypatch.setattr(
        nodes_mod,
        "get_retriever",
        lambda mode="hybrid", k=None: type(
            "R", (), {"invoke": staticmethod(lambda q: [])}
        )(),
    )
    monkeypatch.setattr(nodes_mod, "rerank_docs", lambda q, d, top_n=None: d)
    monkeypatch.setattr(svc, "get_llm", lambda temperature=0.7: _fake_llm("ok"))

    called: list[str] = []

    def boom(*a, **k):
        called.append("load_file")
        raise AssertionError("ask must not call load_file")

    section = ensure_section_insight("u-ask", "s-ask")
    monkeypatch.setattr(section, "load_file", boom)

    mem = MemorySaver()
    graph = builder_mod.build_ask_graph(checkpointer=mem)
    builder_mod._compiled = graph
    builder_mod._checkpointer = mem
    get_session_pool().set_shared_graph(graph, mem)

    stream = svc.ask(
        {
            "query": "你好",
            "uuid": "u-ask",
            "section_id": "s-ask",
            "md": "docs/note.md",
        }
    )
    assert "".join(stream) == "ok"
    resp = stream.response
    assert isinstance(resp, AskResponse)
    assert resp.query_filename == "docs/note.md"
    assert called == []
    sec = ensure_section_insight("u-ask", "s-ask")
    assert any("note.md" in p for p in sec.used_filenames())


def test_finalize_syncs_and_saves(monkeypatch):
    import backend.llm.graph.session_pool as pool_mod
    import backend.llm.insight.store as store_mod

    fake = _FakeRedis()
    monkeypatch.setattr(store_mod, "_client", lambda: fake)
    get_insight_registry().reset()

    monkeypatch.setattr(
        pool_mod,
        "get_history",
        lambda uuid, section_id: _FakeHistory(),
    )
    monkeypatch.setattr(
        "backend.llm.insight.section.delete_section_document_from_opensearch",
        lambda *a, **k: 0,
    )

    pool = AskSessionPool(max_size=5, start_sweeper=False)
    session = pool.get_or_create("u-fin", "s-fin", load_history=False)
    section = ensure_section_insight("u-fin", "s-fin")
    section._filenames = ["a.md", "b.md"]
    section._used_filenames = ["a.md"]
    section.batch_add({"x": "1"})
    session.section_insight = section
    session.append_turn("q", "a", search_query="q")

    session.finalize()
    assert section.filenames() == ["a.md"]
    assert section.used_filenames() == ["a.md"]
    assert store_mod.user_insight_key("u-fin") in fake.data
    assert store_mod.section_insight_key("u-fin", "s-fin") in fake.data
    user_payload = json.loads(fake.data[store_mod.user_insight_key("u-fin")])
    assert user_payload["attrs"]["x"] == "1"
