"""ask interrupt HITL 单元测试。"""

from __future__ import annotations

import pytest
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from backend.llm.graph.builder import build_ask_graph, reset_ask_graph_cache
from backend.llm.graph.interrupt import AskInterruptSignal
from backend.llm.graph.session_pool import get_session_pool
from backend.llm.schemas import (
    AskInterruptAnswerItem,
    AskInterruptResult,
    AskInterruptSubmitParams,
    AskParams,
)


class _FakeHistory:
    def __init__(self, messages: list | None = None):
        self.messages = list(messages or [])
        self.added: list = []

    def add_message(self, message) -> None:
        self.added.append(message)
        self.messages.append(message)

    def add_user_message(self, text: str) -> None:
        self.add_message(HumanMessage(content=text))

    def add_ai_message(self, text: str) -> None:
        self.add_message(AIMessage(content=text))


def _fake_llm(content: str = "最终回答"):
    class _FakeStreamLLM:
        def invoke(self, _messages, config=None, **kwargs):
            return AIMessage(content=content)

        def stream(self, _messages, config=None, **kwargs):
            yield AIMessage(content=content)

    return _FakeStreamLLM()


def _empty_redis(monkeypatch):
    import backend.llm.insight.store as store_mod

    class _EmptyRedis:
        def get(self, key: str):
            return None

        def set(self, *a, **k):
            return None

        def close(self):
            return None

    monkeypatch.setattr(store_mod, "_client", lambda: _EmptyRedis())


def _setup_ask_env(monkeypatch, *, rewrite_fn):
    """先 patch 节点依赖，再 compile 图（图持有 fetch_* 函数引用）。"""
    import backend.llm.graph.builder as builder_mod
    import backend.llm.graph.nodes as nodes_mod
    import backend.llm.graph.session_pool as pool_mod
    from backend.llm.insight.registry import get_insight_registry

    reset_ask_graph_cache()
    monkeypatch.setattr(
        pool_mod, "get_history", lambda uuid, section_id: _FakeHistory()
    )
    monkeypatch.setattr(nodes_mod, "rewrite_query_with_tools", rewrite_fn)
    monkeypatch.setattr(
        nodes_mod, "fetch_section_insight", lambda state: {"insight": ["偏好"]}
    )
    monkeypatch.setattr(nodes_mod, "fetch_user_insight", lambda state: {"insight": []})
    monkeypatch.setattr(
        nodes_mod, "fetch_attachments", lambda state: {"attachment": []}
    )
    _empty_redis(monkeypatch)
    get_insight_registry().reset()

    mem = MemorySaver()
    graph = build_ask_graph(checkpointer=mem)
    builder_mod._compiled = graph
    builder_mod._checkpointer = mem
    get_session_pool().set_shared_graph(graph, mem)
    return mem


def test_ask_interrupt_persists_questions_via_tool(monkeypatch):
    import backend.llm.graph.service as svc
    from backend.llm.insight.registry import get_insight_registry

    def rewrite_interrupt(query, history, *, section, **kwargs):
        section.set_interrupt_questions(
            [{"question": "人数？", "option": {"A": "2人", "B": "多人"}}]
        )
        raise AskInterruptSignal(section.get_interrupt_qa())

    _setup_ask_env(monkeypatch, rewrite_fn=rewrite_interrupt)

    out = svc.ask(
        AskParams(query="推荐餐厅", section_id="s2", uuid="u2", insight_use=False)
    )
    assert isinstance(out, AskInterruptResult)
    assert out.uuid == "u2"
    assert out.section_id == "s2"
    assert out.questions[0].question == "人数？"
    assert out.questions[0].option == {"A": "2人", "B": "多人"}
    qa = get_insight_registry().ensure_section_insight("u2", "s2").get_interrupt_qa()
    assert qa[0]["option"] == {"A": "2人", "B": "多人"}
    assert "result" not in qa[0]
    session = get_session_pool().get_or_create("u2", "s2", load_history=False)
    assert session.pending_ask is not None


def test_submit_applies_result_and_resumes(monkeypatch):
    import backend.llm.graph.nodes as nodes_mod
    import backend.llm.graph.service as svc
    from backend.llm.insight.registry import get_insight_registry

    def rewrite_interrupt(query, history, *, section, **kwargs):
        section.set_interrupt_questions(
            [{"question": "预算？", "option": {"A": "低", "B": "高"}}]
        )
        raise AskInterruptSignal(section.get_interrupt_qa())

    _setup_ask_env(monkeypatch, rewrite_fn=rewrite_interrupt)

    interrupted = svc.ask(
        AskParams(query="去哪吃", section_id="s3", uuid="u3", insight_use=False)
    )
    assert isinstance(interrupted, AskInterruptResult)

    calls: list[str] = []

    def rewrite_ok(query, history, *, section, **kwargs):
        calls.append("rewrite")
        assert section.has_interrupt_answers()
        assert "option" not in section.get_interrupt_qa()[0]
        assert section.get_interrupt_qa()[0]["result"] == "高"
        return "检索查询高预算", "喜欢精致"

    monkeypatch.setattr(nodes_mod, "rewrite_query_with_tools", rewrite_ok)

    docs = [Document(page_content="高档店", metadata={})]

    class FakeRetriever:
        def invoke(self, q: str):
            return docs

    monkeypatch.setattr(
        nodes_mod, "get_retriever", lambda mode="hybrid", k=None: FakeRetriever()
    )
    monkeypatch.setattr(nodes_mod, "rerank_docs", lambda q, d, top_n=None: d)
    monkeypatch.setattr(svc, "get_llm", lambda temperature=0.7: _fake_llm("好的"))
    monkeypatch.setattr(
        svc,
        "run_tool_loop",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("skip tools")),
    )
    monkeypatch.setattr(
        "backend.llm.insight.section.SectionInsight.total_maintain",
        lambda self, turns, *, insight_create_turns=None, on_done=None: (
            on_done() if callable(on_done) else None
        ),
    )

    stream = svc.submit_ask_interrupt(
        AskInterruptSubmitParams(
            uuid="u3",
            section_id="s3",
            answers=[AskInterruptAnswerItem(question="预算？", result="高")],
        )
    )
    text = "".join(stream)
    assert text == "好的"
    assert "rewrite" in calls
    session = get_session_pool().get_or_create("u3", "s3", load_history=False)
    assert session.history[-2].additional_kwargs.get("search_query") == "检索查询高预算"
    assert session.history[-2].additional_kwargs.get("detail") == "喜欢精致"
    assert session.history[-2].content == "去哪吃"
    assert session.history[-2].additional_kwargs.get("interrupt_qa") == [
        {"question": "预算？", "result": "高"}
    ]
    assert (
        get_insight_registry().ensure_section_insight("u3", "s3").get_interrupt_qa()
        == []
    )


def test_submit_without_pending_raises(monkeypatch):
    import backend.llm.graph.service as svc
    from backend.llm.insight.registry import get_insight_registry

    def rewrite_ok(query, history, *, section, **kwargs):
        return query, ""

    _setup_ask_env(monkeypatch, rewrite_fn=rewrite_ok)
    get_insight_registry().reset()
    # 重新 ensure 空会话
    get_session_pool().reset()

    with pytest.raises(ValueError, match="no pending interrupt"):
        svc.submit_ask_interrupt(
            AskInterruptSubmitParams(
                uuid="u4",
                section_id="s4",
                answers=[AskInterruptAnswerItem(question="x", result="y")],
            )
        )


def test_apply_interrupt_answers_replaces_option_with_result():
    from backend.llm.insight.section import SectionInsight

    section = SectionInsight("u", "s")
    section.set_interrupt_questions(
        [{"question": "预算？", "option": {"A": "低", "B": "高"}}]
    )
    section.apply_interrupt_answers([{"question": "预算？", "result": "高"}])
    qa = section.get_interrupt_qa()
    assert qa == [{"question": "预算？", "result": "高"}]
    assert section.has_interrupt_answers()
    assert not section.has_pending_interrupt_questions()


def test_section_insight_redis_omits_interrupt_qa(monkeypatch):
    """save/load 不持久化 interrupt_qa，也不存 pending_ask / pending_enrich。"""
    import json

    import backend.llm.insight.store as store_mod
    from backend.llm.insight.model import UserInsight
    from backend.llm.insight.section import SectionInsight

    saved: dict[str, str] = {}

    class _MemRedis:
        def get(self, key: str):
            raw = saved.get(key)
            return raw.encode("utf-8") if raw is not None else None

        def set(self, key: str, value: str, ex=None):
            saved[key] = value

        def close(self):
            return None

    monkeypatch.setattr(store_mod, "_client", lambda: _MemRedis())

    parent = UserInsight("u-store")
    section = SectionInsight("u-store", "s-store", parent=parent)
    section.set_interrupt_questions(
        [{"question": "预算？", "option": {"A": "低", "B": "高"}}]
    )
    section.save_to_redis()
    payload = json.loads(next(iter(saved.values())))
    assert "interrupt_qa" not in payload
    assert "pending_ask" not in payload
    assert "pending_enrich" not in payload

    loaded = SectionInsight.load_section_from_redis("u-store", "s-store", parent=parent)
    assert loaded is not None
    assert loaded.get_interrupt_qa() == []


def test_new_ask_discards_abandoned_interrupt(monkeypatch):
    """打断后未 submit，再 ask：清空 pending，当作上轮 interrupt 未发生。"""
    import backend.llm.graph.nodes as nodes_mod
    import backend.llm.graph.service as svc
    from backend.llm.insight.registry import get_insight_registry

    def rewrite_interrupt(query, history, *, section, **kwargs):
        section.set_interrupt_questions(
            [{"question": "预算？", "option": {"A": "低", "B": "高"}}]
        )
        raise AskInterruptSignal(section.get_interrupt_qa())

    _setup_ask_env(monkeypatch, rewrite_fn=rewrite_interrupt)

    out1 = svc.ask(
        AskParams(query="去哪吃", section_id="s-disc", uuid="u-disc", insight_use=False)
    )
    assert isinstance(out1, AskInterruptResult)
    session = get_session_pool().get_or_create("u-disc", "s-disc", load_history=False)
    assert session.pending_ask is not None
    assert (
        get_insight_registry()
        .ensure_section_insight("u-disc", "s-disc")
        .has_pending_interrupt_questions()
    )

    def rewrite_ok(query, history, *, section, **kwargs):
        assert not section.has_pending_interrupt_questions()
        return query, ""

    monkeypatch.setattr(nodes_mod, "rewrite_query_with_tools", rewrite_ok)
    docs = [Document(page_content="店", metadata={})]

    class FakeRetriever:
        def invoke(self, q: str):
            return docs

    monkeypatch.setattr(
        nodes_mod, "get_retriever", lambda mode="hybrid", k=None: FakeRetriever()
    )
    monkeypatch.setattr(nodes_mod, "rerank_docs", lambda q, d, top_n=None: d)
    monkeypatch.setattr(svc, "get_llm", lambda temperature=0.7: _fake_llm("新答"))
    monkeypatch.setattr(
        svc,
        "run_tool_loop",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("skip tools")),
    )
    monkeypatch.setattr(
        "backend.llm.insight.section.SectionInsight.total_maintain",
        lambda self, turns, *, insight_create_turns=None, on_done=None: (
            on_done() if callable(on_done) else None
        ),
    )

    stream = svc.ask(
        AskParams(
            query="换个问题", section_id="s-disc", uuid="u-disc", insight_use=False
        )
    )
    assert not isinstance(stream, AskInterruptResult)
    assert "".join(stream) == "新答"
    session = get_session_pool().get_or_create("u-disc", "s-disc", load_history=False)
    # 本轮已结束，pending 已清
    assert session.pending_ask is None
    assert session.pending_enrich == {}
    assert (
        get_insight_registry()
        .ensure_section_insight("u-disc", "s-disc")
        .get_interrupt_qa()
        == []
    )


def test_flush_strips_interrupt_qa(monkeypatch):
    from backend.llm.graph.session_pool import AskSession

    added: list = []

    class _Hist:
        def add_message(self, message) -> None:
            added.append(message)

    monkeypatch.setattr(
        "backend.llm.graph.session_pool.get_history",
        lambda uuid, section_id: _Hist(),
    )
    session = AskSession(uuid="u-flush", section_id="s-flush")
    session.append_turn(
        "原问",
        "答",
        search_query="检索",
        interrupt_qa=[{"question": "预算？", "result": "高"}],
    )
    assert "interrupt_qa" in session.history[0].additional_kwargs
    session.flush_to_redis()
    assert len(added) == 2
    assert "interrupt_qa" not in (added[0].additional_kwargs or {})
    assert added[0].content == "原问"


def test_turns_for_maintain_splices_without_mutating_history():
    from langchain_core.messages import AIMessage, HumanMessage

    from backend.llm.graph.session_pool import _turns_for_maintain

    human = HumanMessage(
        content="去哪吃",
        additional_kwargs={
            "interrupt_qa": [{"question": "预算？", "result": "高"}],
        },
    )
    ai = AIMessage(content="推荐")
    out = _turns_for_maintain([(human, ai)])
    assert human.content == "去哪吃"
    assert out[0][0].content == "去哪吃。追问结果：【预算？：高】"
