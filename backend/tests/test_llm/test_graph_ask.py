"""backend.llm.graph 单元测试（MemorySaver，不连真实 Redis/OpenSearch）。"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from backend.llm.graph.builder import (
    build_ask_graph,
    get_ask_session,
    release_ask_session,
    reset_ask_graph_cache,
)
from backend.llm.graph.router import (
    route_after_attachment,
    route_after_enrich,
    route_after_history,
    route_after_user_insight,
)
from backend.llm.graph.session_pool import AskSessionPool, get_session_pool
from backend.llm.graph.tools import sources_from_docs
from backend.llm.schemas import AskResponse, HistoryMessage, RagSnippet


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


def _fake_llm(content: str = "图回答"):
    """不继承 RunnableLambda，避免 ty 对 stream 签名 override 报错。"""

    class _FakeStreamLLM:
        def invoke(self, _messages, config=None, **kwargs):
            return AIMessage(content=content)

        def stream(self, _messages, config=None, **kwargs):
            yield AIMessage(content=content)

    return _FakeStreamLLM()


def test_route_after_history_empty():
    assert route_after_history({"history": []}) == "retrieve_rerank"
    assert route_after_history({}) == "retrieve_rerank"


def test_route_after_history_with_messages():
    assert (
        route_after_history(
            {"history": [HumanMessage(content="hi"), AIMessage(content="yo")]}
        )
        == "rewrite"
    )


def test_route_after_attachment():
    assert route_after_attachment({}) == "fetch_section_insight"
    assert route_after_attachment({"insight_use": True}) == "fetch_user_insight"
    assert (
        route_after_attachment({"attachment_filenames": ["a.md"]})
        == "fetch_attachments"
    )


def test_route_after_user_insight():
    assert route_after_user_insight({}) == "fetch_section_insight"
    assert route_after_user_insight({"insight_use": True}) == "fetch_user_insight"


def test_route_after_enrich_with_insight_or_attachment():
    assert route_after_enrich({"insight": ["x"]}) == "rewrite"
    assert route_after_enrich({"attachment": ["y"]}) == "rewrite"
    assert route_after_enrich({"history": [], "insight": [], "attachment": []}) == (
        "retrieve_rerank"
    )


def test_sources_from_docs_strips_embedding():
    docs = [
        Document(
            page_content="片段",
            metadata={"name": "Acme", "embedding": [0.1]},
        )
    ]
    sources = sources_from_docs(docs)
    assert sources[0]["content"] == "片段"
    assert "embedding" not in sources[0]["metadata"]


def test_retrieve_writes_sources_to_session_not_state(monkeypatch):
    import backend.llm.graph.builder as builder_mod
    import backend.llm.graph.nodes as nodes_mod
    import backend.llm.graph.session_pool as pool_mod

    reset_ask_graph_cache()
    docs = [
        Document(
            page_content="片段",
            metadata={"name": "Acme", "chunk_index": 0, "embedding": [0.1]},
        )
    ]

    class FakeRetriever:
        def invoke(self, q: str):
            return docs

    monkeypatch.setattr(
        nodes_mod, "get_retriever", lambda mode="hybrid", k=None: FakeRetriever()
    )
    monkeypatch.setattr(nodes_mod, "rerank_docs", lambda q, d, top_n=None: d)
    monkeypatch.setattr(
        pool_mod, "get_history", lambda uuid, section_id: _FakeHistory()
    )
    monkeypatch.setattr(
        nodes_mod, "fetch_section_insight", lambda state: {"insight": []}
    )
    monkeypatch.setattr(nodes_mod, "fetch_user_insight", lambda state: {"insight": []})
    monkeypatch.setattr(
        nodes_mod, "fetch_attachments", lambda state: {"attachment": []}
    )

    mem = MemorySaver()
    graph = build_ask_graph(checkpointer=mem)
    builder_mod._compiled = graph
    builder_mod._checkpointer = mem
    get_session_pool().set_shared_graph(graph, mem)
    session = get_ask_session("u1", "sec-g1", checkpointer=mem)

    final = graph.invoke(
        {
            "query": "问题",
            "section_id": "sec-g1",
            "uuid": "u1",
            "history": [],
            "insight_use": False,
            "attachment_filenames": [],
            "insight": [],
            "attachment": [],
        },
        config={"configurable": {"thread_id": "u1::sec-g1"}},
    )
    assert "sources" not in final
    assert "context" in final
    assert final.get("search_query") == "问题"
    assert len(session.last_sources) == 1
    assert session.last_search_query == "问题"
    assert "embedding" not in session.last_sources[0]["metadata"]


def test_session_pool_lru_flushes_on_evict(monkeypatch):
    import backend.llm.graph.session_pool as pool_mod

    fake_by_key: dict[str, _FakeHistory] = {}

    def fake_get_history(uuid: str, section_id: str) -> _FakeHistory:
        key = f"{uuid}::{section_id}"
        if key not in fake_by_key:
            fake_by_key[key] = _FakeHistory()
        return fake_by_key[key]

    monkeypatch.setattr(pool_mod, "get_history", fake_get_history)
    pool = AskSessionPool(max_size=2, start_sweeper=False)
    s1 = pool.get_or_create("a", "s1")
    s1.append_turn(
        "q1",
        "a1",
        search_query="q1",
        filename="",
        insight_create=True,
        sources=[{"content": "c1", "metadata": {}}],
    )
    assert fake_by_key.get("a::s1") is None or fake_by_key["a::s1"].added == []
    s2 = pool.get_or_create("b", "s2")
    s2.append_turn("q2", "a2", search_query="q2", filename="", sources=[])
    _s3 = pool.get_or_create("c", "s3")
    assert "a::s1" not in pool._sessions
    flushed = fake_by_key["a::s1"].added
    assert len(flushed) == 2
    assert flushed[0].content == "q1"
    assert flushed[0].additional_kwargs["search_query"] == "q1"
    assert flushed[0].additional_kwargs["insight_create"] is True
    assert flushed[0].additional_kwargs["used"] is False
    assert flushed[1].additional_kwargs["sources"][0]["content"] == "c1"
    assert flushed[1].additional_kwargs["used"] is False


def test_session_pool_idle_sweep(monkeypatch):
    import backend.llm.graph.session_pool as pool_mod

    fake_by_key: dict[str, _FakeHistory] = {}

    def fake_get_history(uuid: str, section_id: str) -> _FakeHistory:
        key = f"{uuid}::{section_id}"
        if key not in fake_by_key:
            fake_by_key[key] = _FakeHistory()
        return fake_by_key[key]

    monkeypatch.setattr(pool_mod, "get_history", fake_get_history)
    pool = AskSessionPool(max_size=5, idle_seconds=10, start_sweeper=False)
    s1 = pool.get_or_create("a", "s1")
    s1.append_turn("q", "a", search_query="q")
    s1.last_used = 0.0
    released = pool.sweep_idle(now=100.0)
    assert released == ["a::s1"]
    assert "a::s1" not in pool._sessions
    assert len(fake_by_key["a::s1"].added) == 2


def test_graph_ask_stream_service(monkeypatch):
    import backend.llm.graph.builder as builder_mod
    import backend.llm.graph.nodes as nodes_mod
    import backend.llm.graph.service as svc
    import backend.llm.graph.session_pool as pool_mod

    prior = [
        HumanMessage(
            content="上次问过",
            additional_kwargs={
                "search_query": "上次问过",
                "filename": "",
                "insight_create": False,
            },
        ),
        AIMessage(
            content="上次答过",
            additional_kwargs={"sources": [{"content": "旧资料", "metadata": {}}]},
        ),
    ]
    redis_hist = _FakeHistory(prior)
    docs = [Document(page_content="服务很好", metadata={"polarity": "positive"})]

    class FakeRetriever:
        def invoke(self, q: str):
            assert q == "改写后的查询"
            return docs

    reset_ask_graph_cache()
    monkeypatch.setattr(pool_mod, "get_history", lambda uuid, section_id: redis_hist)
    monkeypatch.setattr(
        nodes_mod, "rewrite_query", lambda q, h, **kwargs: "改写后的查询"
    )
    monkeypatch.setattr(
        nodes_mod, "get_retriever", lambda mode="hybrid", k=None: FakeRetriever()
    )
    monkeypatch.setattr(nodes_mod, "rerank_docs", lambda q, d, top_n=None: d)
    monkeypatch.setattr(svc, "get_llm", lambda temperature=0.7: _fake_llm("适合"))
    monkeypatch.setattr(
        nodes_mod, "fetch_section_insight", lambda state: {"insight": []}
    )
    monkeypatch.setattr(nodes_mod, "fetch_user_insight", lambda state: {"insight": []})
    monkeypatch.setattr(
        nodes_mod, "fetch_attachments", lambda state: {"attachment": []}
    )

    import backend.llm.insight.store as store_mod

    class _EmptyRedis:
        def get(self, key: str):
            return None

        def set(self, *a, **k):
            return None

        def close(self):
            return None

    monkeypatch.setattr(store_mod, "_client", lambda: _EmptyRedis())
    from backend.llm.insight.registry import get_insight_registry

    get_insight_registry().reset()

    mem = MemorySaver()
    graph = build_ask_graph(checkpointer=mem)
    builder_mod._compiled = graph
    builder_mod._checkpointer = mem
    get_session_pool().set_shared_graph(graph, mem)

    stream = svc.ask(
        {
            "query": "适合约会吗",
            "section_id": "sec-1",
            "uuid": "req-9",
            "insight_create": True,
            "insight_use": False,
        }
    )
    text = "".join(stream)
    assert text == "适合"
    resp = stream.response
    assert isinstance(resp, AskResponse)
    assert resp.uuid == "req-9"
    assert resp.answer == "适合"
    assert resp.query_filename == ""
    assert len(resp.sources) == 1
    assert resp.sources[0].content == "服务很好"
    assert "history" not in AskResponse.model_fields

    hist = svc.get_ask_history(uuid="req-9", section_id="sec-1")
    assert hist.uuid == "req-9"
    assert hist.section_id == "sec-1"
    assert len(hist.history) == 4  # prior 2 + 本轮 2
    assert hist.history[0] == HistoryMessage(
        role="user",
        content="上次问过",
        filename="",
        insight_create=False,
        insight_use=False,
        sources=None,
    )
    assert hist.history[1].role == "assistant"
    assert hist.history[1].content == "上次答过"
    assert hist.history[1].sources == [RagSnippet(content="旧资料", metadata={})]
    assert hist.history[1].insight_create is None
    assert hist.history[1].insight_use is None
    assert hist.history[2].content == "适合约会吗"
    assert hist.history[2].insight_create is True
    assert hist.history[2].insight_use is False
    assert hist.insight_create is True
    assert hist.insight_use is False
    dumped = hist.history[0].model_dump()
    assert "search_query" not in dumped
    assert "insight_create" in dumped
    assert "insight_use" in dumped
    assert "used" not in dumped

    # ask 后仍 pending；release 才刷 Redis
    assert len(redis_hist.added) == 0
    session = get_ask_session("req-9", "sec-1", checkpointer=mem)
    assert len(session.pending_turns) == 1

    release_ask_session("req-9", "sec-1")
    assert len(redis_hist.added) == 2
    assert redis_hist.added[0].content == "适合约会吗"
    assert redis_hist.added[0].additional_kwargs["search_query"] == "改写后的查询"
    assert redis_hist.added[0].additional_kwargs["insight_create"] is True
    assert redis_hist.added[0].additional_kwargs["insight_use"] is False
    assert redis_hist.added[0].additional_kwargs["used"] is False
    assert redis_hist.added[1].content == "适合"
    assert redis_hist.added[1].additional_kwargs["used"] is False


def test_delete_ask_history_and_by_uuid(monkeypatch):
    import backend.llm.graph.service as svc
    import backend.llm.graph.session_pool as pool_mod
    import backend.llm.session.history as history_mod

    class FakeRedisHistory:
        def __init__(self, messages=None):
            self.messages = list(messages or [])
            self.cleared = False

        def clear(self) -> None:
            self.cleared = True
            self.messages.clear()

        def add_message(self, message) -> None:
            self.messages.append(message)

    store: dict[str, FakeRedisHistory] = {
        "u1::s1": FakeRedisHistory([HumanMessage(content="a")]),
        "u1::s2": FakeRedisHistory([HumanMessage(content="b")]),
        "u2::s9": FakeRedisHistory([HumanMessage(content="c")]),
    }

    def fake_get_history(uuid: str, section_id: str) -> FakeRedisHistory:
        key = f"{uuid}::{section_id}"
        if key not in store:
            store[key] = FakeRedisHistory()
        return store[key]

    monkeypatch.setattr(pool_mod, "get_history", fake_get_history)
    monkeypatch.setattr(history_mod, "get_history", fake_get_history)
    monkeypatch.setattr(
        history_mod,
        "list_history_session_ids_for_uuid",
        lambda uuid: sorted(k for k in store if k.startswith(f"{uuid}::")),
    )

    reset_ask_graph_cache()
    pool = get_session_pool()
    s = pool.get_or_create("u1", "s1")
    s.history = [HumanMessage(content="mem")]

    out = svc.delete_ask_history(uuid="u1", section_id="s1")
    assert out.deleted_sessions == 1
    assert out.section_ids == ["s1"]
    assert store["u1::s1"].cleared is True
    assert "u1::s1" not in pool._sessions

    out2 = svc.delete_ask_histories_by_uuid(uuid="u1")
    assert out2.section_id is None
    assert set(out2.section_ids) == {"s1", "s2"}
    assert store["u1::s2"].cleared is True
    assert store["u2::s9"].cleared is False
