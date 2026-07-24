"""洞察维护状态机 / 历史窗口 / 路径 / 门面读写。"""

from __future__ import annotations

import threading
import time

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.llm.graph.history_window import (
    filter_chat_messages,
    iter_complete_turns,
    select_history_window,
)
from backend.llm.graph.nodes import history_snapshot
from backend.llm.graph.session_pool import (
    MAINTAIN_BATCH_TURNS,
    MAINTAIN_TRIGGER_TURNS,
    AskSession,
    AskSessionPool,
)
from backend.llm.insight.registry import ensure_section_insight, get_insight_registry
from backend.rag.document.paths import normalize_backend_path


class _FakeHistory:
    def __init__(self, messages: list | None = None):
        self.messages = list(messages or [])
        self.added: list = []

    def add_message(self, message) -> None:
        self.added.append(message)
        self.messages.append(message)

    def clear(self) -> None:
        self.messages.clear()


class _FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.data[key] = value

    def get(self, key: str) -> str | None:
        return self.data.get(key)

    def delete(self, *keys: str) -> int:
        n = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                n += 1
        return n

    def scan_iter(self, match: str | None = None, count: int = 200):
        import fnmatch

        for key in list(self.data):
            if match is None or fnmatch.fnmatch(key, match):
                yield key

    def close(self) -> None:
        return None


def _turn(i: int, *, used: bool = False, insight_create: bool = False):
    human = HumanMessage(
        content=f"q{i}",
        additional_kwargs={
            "search_query": f"q{i}",
            "filename": "",
            "insight_create": insight_create,
            "insight_use": False,
            "used": used,
        },
    )
    ai = AIMessage(
        content=f"a{i}",
        additional_kwargs={"sources": [], "used": used},
    )
    return human, ai


def test_filter_chat_messages_drops_system():
    msgs = [
        SystemMessage(content="sys"),
        HumanMessage(content="u"),
        AIMessage(content="a"),
    ]
    out = filter_chat_messages(msgs)
    assert len(out) == 2
    assert all(not isinstance(m, SystemMessage) for m in out)


def test_history_snapshot_user_assistant_only():
    msgs = [
        SystemMessage(content="sys"),
        HumanMessage(content="u", additional_kwargs={"used": False}),
        AIMessage(content="a", additional_kwargs={"used": False}),
    ]
    snap = history_snapshot(msgs)
    assert [x["role"] for x in snap] == ["user", "assistant"]


def test_normalize_backend_path_forces_prefix():
    from backend.config.paths import REPO_ROOT

    target = REPO_ROOT / "backend" / "tmp_norm_test.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text("x", encoding="utf-8")
        rel = normalize_backend_path(str(target))
        assert rel is not None
        assert rel.startswith("./backend/")
        assert rel.endswith("tmp_norm_test.md")
        assert normalize_backend_path("outside/x.md") is None
    finally:
        if target.exists():
            target.unlink()


def test_load_history_window_unused_tail_pad_to_3():
    turns = []
    for i in range(5):
        h, a = _turn(i, used=(i < 3))
        turns.extend([h, a])
    # used used used unused unused → 尾部 2 unused，补 1 个 used → 3 轮
    window = select_history_window(turns, min_turns=3)
    complete = iter_complete_turns(window)
    assert len(complete) == 3
    assert [str(h.content) for h, _ in complete] == ["q2", "q3", "q4"]


def test_maintain_state_machine_flush_pop_merge(monkeypatch):
    import backend.llm.graph.session_pool as pool_mod
    import backend.llm.insight.store as store_mod

    fake = _FakeRedis()
    monkeypatch.setattr(store_mod, "_client", lambda: fake)
    get_insight_registry().reset()

    redis_hist = _FakeHistory()
    monkeypatch.setattr(pool_mod, "get_history", lambda uuid, section_id: redis_hist)

    section = ensure_section_insight("u-m", "s-m")
    section.set_review("old")
    section.add_facts(items=["f0"])

    session = AskSession(uuid="u-m", section_id="s-m", section_insight=section)
    for i in range(MAINTAIN_TRIGGER_TURNS):
        session.append_turn(
            f"q{i}",
            f"a{i}",
            search_query=f"q{i}",
            insight_create=(i == 0),
            used=False,
        )

    done_event = threading.Event()

    def fake_total(self, turns, *, insight_create_turns=None, on_done=None):
        self.set_review("new-review")
        self.add_facts(items=["f-new"])
        self.batch_add_section({"k": "v"})
        if insight_create_turns:
            self.batch_add({"user_k": "user_v"})
        if callable(on_done):
            on_done()
        done_event.set()

    monkeypatch.setattr(
        type(section),
        "total_maintain",
        fake_total,
    )
    monkeypatch.setattr(
        type(section),
        "split_and_store_section",
        lambda self: 0,
    )
    monkeypatch.setattr(
        type(section),
        "split_and_store",
        lambda self: 0,
    )

    session.maintain()
    assert session.maintain_flag == "active"
    assert done_event.wait(timeout=2.0)

    # 再次 maintain：处理 done
    session.maintain()
    assert session.maintain_flag == "idle"
    assert len(iter_complete_turns(session.history)) == (
        MAINTAIN_TRIGGER_TURNS - MAINTAIN_BATCH_TURNS
    )
    assert section.get_review() == "new-review"
    assert "f-new" in section.get_facts()
    assert section.section_as_dict().get("k") == "v"
    assert section.as_dict().get("user_k") == "user_v"
    assert len(redis_hist.added) == MAINTAIN_BATCH_TURNS * 2
    assert all(m.additional_kwargs.get("used") is True for m in redis_hist.added)


def test_maintain_active_returns(monkeypatch):
    session = AskSession(uuid="u", section_id="s")
    session.maintain_flag = "active"
    session.maintain()
    assert session.maintain_flag == "active"


def test_insight_facade_get_update(monkeypatch):
    import backend.llm.graph.service as svc
    import backend.llm.insight.store as store_mod

    fake = _FakeRedis()
    monkeypatch.setattr(store_mod, "_client", lambda: fake)
    get_insight_registry().reset()
    monkeypatch.setattr(
        "backend.llm.graph.service.delete_insight_from_opensearch",
        lambda *a, **k: 0,
    )
    monkeypatch.setattr(
        "backend.llm.graph.service.delete_section_insight_from_opensearch",
        lambda *a, **k: 0,
    )
    monkeypatch.setattr(
        "backend.llm.insight.model.UserInsight.split_and_store",
        lambda self: 0,
    )
    monkeypatch.setattr(
        "backend.llm.insight.section.SectionInsight.split_and_store_section",
        lambda self: 0,
    )

    assert svc.update_user_insight_attrs("u-f", {"a": "1", "b": "2"}) is True
    assert svc.get_user_insight("u-f") == {"a": "1", "b": "2"}
    # 覆写：旧键消失
    assert svc.update_user_insight_attrs("u-f", {"a": "9"}) is True
    assert svc.get_user_insight("u-f") == {"a": "9"}

    assert svc.update_section_insight_attrs("u-f", "s1", {"b": "2", "c": "3"}) is True
    assert svc.get_section_insight("u-f", "s1") == {"b": "2", "c": "3"}
    assert svc.update_section_insight_attrs("u-f", "s1", {"b": "x"}) is True
    assert svc.get_section_insight("u-f", "s1") == {"b": "x"}

    assert svc.update_section_facts("u-f", "s1", ["x", "y"]) is True
    assert svc.get_section_facts("u-f", "s1") == ["x", "y"]
    assert svc.update_section_facts("u-f", "s1", ["z"]) is True
    assert svc.get_section_facts("u-f", "s1") == ["z"]

    assert svc.set_section_review("u-f", "s1", "hello") is True
    assert svc.get_section_review("u-f", "s1") == "hello"

    # delete section：只清 attrs，保留 facts/review
    assert svc.delete_section_insight("u-f", "s1") is True
    assert svc.get_section_insight("u-f", "s1") == {}
    assert svc.get_section_facts("u-f", "s1") == ["z"]
    assert svc.get_section_review("u-f", "s1") == "hello"
    sec_key = store_mod.section_insight_key("u-f", "s1")
    assert sec_key in fake.data
    import json

    payload = json.loads(fake.data[sec_key])
    assert payload["section_attrs"] == {}
    assert payload["facts"] == ["z"]
    assert payload["review"] == "hello"

    assert svc.delete_user_insight("u-f") is True
    assert svc.get_user_insight("u-f") == {}
    user_key = store_mod.user_insight_key("u-f")
    assert user_key in fake.data
    assert json.loads(fake.data[user_key])["attrs"] == {}


def test_set_review_truncates_150(monkeypatch):
    import backend.llm.insight.store as store_mod

    monkeypatch.setattr(store_mod, "_client", lambda: _FakeRedis())
    get_insight_registry().reset()
    section = ensure_section_insight("u-t", "s-t")
    long = "字" * 200
    section.set_review(long)
    assert len(section.get_review()) == 150


def test_clone_and_merge_replica(monkeypatch):
    import backend.llm.insight.store as store_mod

    monkeypatch.setattr(store_mod, "_client", lambda: _FakeRedis())
    get_insight_registry().reset()
    live = ensure_section_insight("u-c", "s-c")
    live.set_review("r1")
    live.batch_add({"u": "1"})
    live.batch_add_section({"s": "1"})
    replica = live.clone_for_maintain()
    replica.set_review("r2")
    replica.batch_add({"u": "2"})
    replica.batch_add_section({"s": "2"})
    # 维护中 live 不变
    assert live.get_review() == "r1"
    sec_ch, user_ch = live.merge_from_maintain_replica(replica)
    assert sec_ch and user_ch
    assert live.get_review() == "r2"
    assert live.as_dict()["u"] == "2"
    assert live.section_as_dict()["s"] == "2"


def test_release_returns_immediately_and_queues_same_section(monkeypatch):
    import backend.llm.graph.session_pool as pool_mod
    import backend.llm.insight.store as store_mod

    monkeypatch.setattr(store_mod, "_client", lambda: _FakeRedis())
    get_insight_registry().reset()

    redis_hist = _FakeHistory()
    monkeypatch.setattr(pool_mod, "get_history", lambda u, s: redis_hist)

    hold = threading.Event()
    started = threading.Event()

    def slow_total(self, turns, *, insight_create_turns=None, on_done=None):
        started.set()
        hold.wait(timeout=5.0)
        if callable(on_done):
            on_done()

    monkeypatch.setattr(
        "backend.llm.insight.section.SectionInsight.total_maintain",
        slow_total,
    )

    pool = AskSessionPool(max_size=5, start_sweeper=False)
    session = pool.get_or_create("u-rel", "s-a", load_history=False)
    section = ensure_section_insight("u-rel", "s-a")
    session.section_insight = section
    for i in range(2):
        session.append_turn(f"q{i}", f"a{i}", search_query=f"q{i}")

    assert pool.release("u-rel", "s-a") is True
    assert "u-rel::s-a" not in pool._sessions
    assert started.wait(timeout=2.0)

    blocked: list[bool] = []

    def other_request() -> None:
        pool_mod.wait_section_ready("u-rel", "s-a")
        blocked.append(True)

    t = threading.Thread(target=other_request)
    t.start()
    time.sleep(0.1)
    assert blocked == []
    hold.set()
    t.join(timeout=2.0)
    assert blocked == [True]
    pool_mod.wait_section_ready("u-rel", "s-a")
    assert any(m.additional_kwargs.get("used") for m in redis_hist.messages)


def test_release_other_section_not_blocked(monkeypatch):
    import backend.llm.graph.session_pool as pool_mod
    import backend.llm.insight.store as store_mod

    monkeypatch.setattr(store_mod, "_client", lambda: _FakeRedis())
    get_insight_registry().reset()
    monkeypatch.setattr(pool_mod, "get_history", lambda u, s: _FakeHistory())

    hold = threading.Event()

    def slow_total(self, turns, *, insight_create_turns=None, on_done=None):
        hold.wait(timeout=5.0)
        if callable(on_done):
            on_done()

    monkeypatch.setattr(
        "backend.llm.insight.section.SectionInsight.total_maintain",
        slow_total,
    )

    pool = AskSessionPool(max_size=5, start_sweeper=False)
    sa = pool.get_or_create("u-rel2", "s-a", load_history=False)
    sa.section_insight = ensure_section_insight("u-rel2", "s-a")
    sa.append_turn("q", "a", search_query="q")
    pool.release("u-rel2", "s-a")

    # 同 uuid 不同 section 不应阻塞
    t0 = time.monotonic()
    pool_mod.wait_section_ready("u-rel2", "s-b")
    assert time.monotonic() - t0 < 0.5
    hold.set()
    pool_mod.wait_section_ready("u-rel2", "s-a")


def test_release_empty_pool_true():

    pool = AskSessionPool(max_size=5, start_sweeper=False)
    assert pool.release("no-such", "sec") is True


def test_release_maintain_without_seven_gate(monkeypatch):
    import backend.llm.graph.session_pool as pool_mod
    import backend.llm.insight.store as store_mod

    monkeypatch.setattr(store_mod, "_client", lambda: _FakeRedis())
    get_insight_registry().reset()
    redis_hist = _FakeHistory()
    monkeypatch.setattr(pool_mod, "get_history", lambda u, s: redis_hist)

    called: list[int] = []

    def fake_total(self, turns, *, insight_create_turns=None, on_done=None):
        called.append(len(list(turns)))
        if callable(on_done):
            on_done()

    monkeypatch.setattr(
        "backend.llm.insight.section.SectionInsight.total_maintain",
        fake_total,
    )

    pool = AskSessionPool(max_size=5, start_sweeper=False)
    session = pool.get_or_create("u-rel3", "s1", load_history=False)
    session.section_insight = ensure_section_insight("u-rel3", "s1")
    # 少于 7 轮，ask 路径不会维护，但 release 会
    for i in range(3):
        session.append_turn(f"q{i}", f"a{i}", search_query=f"q{i}")
    assert pool.release("u-rel3", "s1") is True
    pool_mod.wait_section_ready("u-rel3", "s1")
    assert called == [3]


def test_get_section_review_falls_back_to_first_memory_query(monkeypatch):
    import backend.llm.graph.service as svc
    import backend.llm.graph.session_pool as pool_mod
    import backend.llm.insight.store as store_mod

    monkeypatch.setattr(store_mod, "_client", lambda: _FakeRedis())
    get_insight_registry().reset()
    pool_mod.get_session_pool().reset()

    section = ensure_section_insight("u-rev", "s1")
    assert section.get_review() == ""
    assert svc.get_section_review("u-rev", "s1") == ""

    pool = pool_mod.get_session_pool()
    session = pool.get_or_create("u-rev", "s1", load_history=False)
    session.section_insight = section
    session.append_turn("第一问", "答", search_query="第一问")
    session.append_turn("第二问", "答2", search_query="第二问")
    assert svc.get_section_review("u-rev", "s1") == "第一问"
    assert section.as_get_review_tool().invoke({}) == "第一问"

    section.set_review("正式摘要")
    assert svc.get_section_review("u-rev", "s1") == "正式摘要"


def test_occupied_skips_other_section_ask_maintain(monkeypatch):
    import backend.llm.insight.store as store_mod

    monkeypatch.setattr(store_mod, "_client", lambda: _FakeRedis())
    get_insight_registry().reset()

    sa = ensure_section_insight("u-occ", "s-a")
    sb = ensure_section_insight("u-occ", "s-b")
    parent = sa._parent
    assert parent is sb._parent

    pool = AskSessionPool(max_size=5, start_sweeper=False)
    sess_a = pool.get_or_create("u-occ", "s-a", load_history=False)
    sess_b = pool.get_or_create("u-occ", "s-b", load_history=False)
    sess_a.section_insight = sa
    sess_b.section_insight = sb
    for i in range(MAINTAIN_TRIGGER_TURNS):
        sess_a.append_turn(f"qa{i}", f"aa{i}", search_query=f"qa{i}")
        sess_b.append_turn(f"qb{i}", f"ab{i}", search_query=f"qb{i}")

    hold = threading.Event()
    started = threading.Event()

    def slow_total(self, turns, *, insight_create_turns=None, on_done=None):
        started.set()
        hold.wait(timeout=5.0)
        if callable(on_done):
            on_done()

    monkeypatch.setattr(
        "backend.llm.insight.section.SectionInsight.total_maintain",
        slow_total,
    )

    sess_a.maintain()
    assert started.wait(timeout=2.0)
    assert parent.occupied is True

    flag_before = sess_b.maintain_flag
    sess_b.maintain()
    assert sess_b.maintain_flag == flag_before
    assert sess_b._maintain_replica is None

    hold.set()
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline and sess_a.maintain_flag != "done":
        time.sleep(0.05)
    sess_a.maintain()
    assert parent.occupied is False

    sess_b.maintain()
    assert parent.occupied is True or sess_b.maintain_flag in ("active", "done", "idle")
    if sess_b.maintain_flag == "active":
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline and sess_b.maintain_flag != "done":
            time.sleep(0.05)
    if sess_b.maintain_flag == "done":
        sess_b.maintain()
    assert parent.occupied is False


def test_release_waits_on_occupied(monkeypatch):
    import backend.llm.graph.session_pool as pool_mod
    import backend.llm.insight.store as store_mod

    monkeypatch.setattr(store_mod, "_client", lambda: _FakeRedis())
    get_insight_registry().reset()
    monkeypatch.setattr(pool_mod, "get_history", lambda u, s: _FakeHistory())

    section = ensure_section_insight("u-occ2", "s1")
    parent = section._parent
    assert parent.try_acquire_occupied() is True

    pool = AskSessionPool(max_size=5, start_sweeper=False)
    session = pool.get_or_create("u-occ2", "s1", load_history=False)
    session.section_insight = section
    session.append_turn("q", "a", search_query="q")

    called = threading.Event()

    def fake_total(self, turns, *, insight_create_turns=None, on_done=None):
        called.set()
        if callable(on_done):
            on_done()

    monkeypatch.setattr(
        "backend.llm.insight.section.SectionInsight.total_maintain",
        fake_total,
    )

    assert pool.release("u-occ2", "s1") is True
    time.sleep(0.15)
    assert called.is_set() is False
    parent.release_occupied()
    assert called.wait(timeout=2.0)
    pool_mod.wait_section_ready("u-occ2", "s1")


def test_attrs_len_gates_split_and_search(monkeypatch):
    from backend.config import settings
    from backend.llm.insight.model import UserInsight, format_attrs_concat
    from backend.llm.insight.section import SectionInsight
    import backend.llm.insight.model as model_mod
    import backend.llm.insight.section as sec_mod

    monkeypatch.setattr(settings, "insight_chunk_size", 100)
    u = UserInsight("u-len")
    u.batch_add({"a": "1", "b": "2"})
    expected = format_attrs_concat(u.as_dict())
    assert u.attrs_len == len(expected)
    assert u.attrs_len < 200

    os_calls = {"n": 0}
    monkeypatch.setattr(
        model_mod,
        "index_insight_chunks",
        lambda *a, **k: os_calls.__setitem__("n", os_calls["n"] + 1) or (1, []),
    )
    assert u.split_and_store() == 0
    assert os_calls["n"] == 0
    assert u.search("q") == expected

    s = SectionInsight("u-len", "s1", parent=u)
    s.batch_add_section({"x": "y"})
    sec_expected = format_attrs_concat(s.section_as_dict())
    assert s.attrs_len == len(sec_expected)
    monkeypatch.setattr(
        sec_mod,
        "index_section_insight_chunks",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("should skip")),
    )
    assert s.split_and_store_section() == 0
    assert s.search_section("q") == sec_expected

    monkeypatch.setattr(settings, "insight_chunk_size", 1)
    u2 = UserInsight("u-len2")
    u2.batch_add({"k": "vv"})
    assert u2.attrs_len >= 2
    called = {"n": 0}

    def fake_search(*a, **k):
        called["n"] += 1
        return "os-hit"

    monkeypatch.setattr(model_mod, "search_insight_text", fake_search)
    u2.last_chunk_size = 1
    assert u2.search("q") == "os-hit"
    assert called["n"] == 1
