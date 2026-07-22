"""LLM pipeline.rag_pipeline 单元测试。"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda


def _fake_llm():
    def _call(_messages):
        return AIMessage(content="带来源的回答")

    return RunnableLambda(_call)


class _FakeHistory:
    def __init__(self):
        self.messages: list = []
        self.user: list[str] = []
        self.ai: list[str] = []

    def add_user_message(self, text: str) -> None:
        self.user.append(text)

    def add_ai_message(self, text: str) -> None:
        self.ai.append(text)


def test_answer_query(monkeypatch):
    import backend.llm.pipeline.rag_pipeline as pipe

    class FakeChain:
        def invoke(self, payload, config=None):
            assert payload == {"query": "你好"}
            assert config is not None
            assert config["configurable"]["session_id"] == "u1::s1"
            return "链回答"

    monkeypatch.setattr(pipe, "build_full_rag_chain", lambda: FakeChain())
    assert pipe.answer_query("你好", "s1", "u1") == "链回答"


def test_stream_answer_query(monkeypatch):
    import backend.llm.pipeline.rag_pipeline as pipe

    class FakeChain:
        def stream(self, payload, config=None):
            assert payload["query"] == "流式"
            assert config is not None
            assert config["configurable"]["session_id"] == "u2::s2"
            yield "一"
            yield "二"

    monkeypatch.setattr(pipe, "build_full_rag_chain", lambda: FakeChain())
    assert "".join(pipe.stream_answer_query("流式", "s2", "u2")) == "一二"


def test_answer_query_with_sources(monkeypatch):
    import backend.llm.pipeline.rag_pipeline as pipe
    from langchain_core.messages import AIMessage, HumanMessage

    hist = _FakeHistory()
    hist.messages = [
        HumanMessage(content="上一问"),
        AIMessage(content="上一答"),
    ]
    docs = [
        Document(
            page_content="片段内容",
            metadata={"name": "Acme", "polarity": "positive", "chunk_index": 0},
        )
    ]

    monkeypatch.setattr(pipe, "get_history", lambda uuid, section_id: hist)
    monkeypatch.setattr(pipe, "retrieve_rerank_docs", lambda inputs: docs)
    monkeypatch.setattr(pipe, "get_llm", lambda temperature=0.2: _fake_llm())

    result = pipe.answer_query_with_sources("问题", "sec-9", "user-1")
    assert isinstance(result, pipe.RagAnswer)
    assert result.answer == "带来源的回答"
    assert result.query == "问题"
    assert result.section_id == "sec-9"
    assert result.sources[0]["content"] == "片段内容"
    assert result.sources[0]["metadata"]["name"] == "Acme"
    assert result.history == [
        {"role": "user", "content": "上一问"},
        {"role": "assistant", "content": "上一答"},
    ]
    assert hist.user == ["问题"]
    assert hist.ai == ["带来源的回答"]
