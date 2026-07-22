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
from backend.llm.graph.router import route_after_history
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
    pool = AskSessionPool(max_size=2)
    s1 = pool.get_or_create("a", "s1")
    s1.append_turn(
        "q1",
        "a1",
        search_query="q1",
        filename="",
        sources=[{"content": "c1", "metadata": {}}],
    )
    s2 = pool.get_or_create("b", "s2")
    s2.append_turn("q2", "a2", search_query="q2", filename="", sources=[])
    _s3 = pool.get_or_create("c", "s3")
    assert "a::s1" not in pool._sessions
    flushed = fake_by_key["a::s1"].added
    assert len(flushed) == 2
    assert flushed[0].content == "q1"
    assert flushed[0].additional_kwargs["search_query"] == "q1"
    assert flushed[1].additional_kwargs["sources"][0]["content"] == "c1"


def test_graph_ask_stream_service(monkeypatch):
    import backend.llm.graph.builder as builder_mod
    import backend.llm.graph.nodes as nodes_mod
    import backend.llm.graph.service as svc
    import backend.llm.graph.session_pool as pool_mod

    prior = [
        HumanMessage(
            content="上次问过",
            additional_kwargs={"search_query": "上次问过", "filename": ""},
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
    monkeypatch.setattr(nodes_mod, "rewrite_query", lambda q, h: "改写后的查询")
    monkeypatch.setattr(
        nodes_mod, "get_retriever", lambda mode="hybrid", k=None: FakeRetriever()
    )
    monkeypatch.setattr(nodes_mod, "rerank_docs", lambda q, d, top_n=None: d)
    monkeypatch.setattr(svc, "get_llm", lambda temperature=0.7: _fake_llm("适合"))

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
    assert resp.history[0] == HistoryMessage(
        role="user",
        content="上次问过",
        filename="",
        sources=None,
    )
    assert resp.history[1].role == "assistant"
    assert resp.history[1].content == "上次答过"
    assert resp.history[1].sources == [RagSnippet(content="旧资料", metadata={})]
    dumped = resp.history[0].model_dump()
    assert "search_query" not in dumped

    # 每轮结束已刷 Redis
    assert len(redis_hist.added) == 2
    assert redis_hist.added[0].content == "适合约会吗"
    assert redis_hist.added[0].additional_kwargs["search_query"] == "改写后的查询"
    assert redis_hist.added[1].content == "适合"

    session = get_ask_session("req-9", "sec-1", checkpointer=mem)
    assert session.pending_turns == []

    release_ask_session("req-9", "sec-1")
    assert len(redis_hist.added) == 2
