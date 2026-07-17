"""LLM 客户端单元测试（mock ChatOpenAI）。"""

from __future__ import annotations

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage


class _FakeLLM:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.tools = None

    def invoke(self, messages, **kwargs):
        return AIMessage(content="ok")

    def stream(self, messages, **kwargs):
        yield AIMessageChunk(content="he")
        yield AIMessageChunk(content="llo")

    def bind_tools(self, tools):
        self.tools = list(tools)
        return self


def test_get_llm_passes_settings(monkeypatch):
    import backend.LLM.client.llm as llm_mod

    captured = {}

    def fake_chat_openai(**kwargs):
        captured.update(kwargs)
        return _FakeLLM(**kwargs)

    monkeypatch.setattr(llm_mod, "ChatOpenAI", fake_chat_openai)
    llm = llm_mod.get_llm(temperature=0.2)
    assert captured["temperature"] == 0.2
    assert captured["model"] == llm_mod.settings.llm_model
    assert isinstance(llm, _FakeLLM)


def test_invoke_llm(monkeypatch):
    import backend.LLM.client.llm as llm_mod

    monkeypatch.setattr(llm_mod, "get_llm", lambda temperature=0.2: _FakeLLM())
    assert llm_mod.invoke_llm("hi") == "ok"
    assert llm_mod.invoke_llm([HumanMessage(content="hi")]) == "ok"


def test_stream_llm(monkeypatch):
    import backend.LLM.client.llm as llm_mod

    monkeypatch.setattr(llm_mod, "get_llm", lambda temperature=0.2: _FakeLLM())
    assert "".join(llm_mod.stream_llm("hi")) == "hello"


def test_get_llm_with_tools(monkeypatch):
    import backend.LLM.client.llm as llm_mod

    fake = _FakeLLM()
    monkeypatch.setattr(llm_mod, "get_llm", lambda temperature=0.2: fake)

    def dummy_tool(x: int) -> int:
        """add one"""
        return x + 1

    bound = llm_mod.get_llm_with_tools([dummy_tool])
    assert getattr(bound, "tools") == [dummy_tool]


def test_invoke_and_stream_with_tools(monkeypatch):
    import backend.LLM.client.llm as llm_mod

    fake = _FakeLLM()
    monkeypatch.setattr(llm_mod, "get_llm", lambda temperature=0.2: fake)

    def dummy_tool(x: int) -> int:
        """add one"""
        return x + 1

    msg = llm_mod.invoke_with_tools("hi", [dummy_tool])
    assert isinstance(msg, AIMessage)
    assert msg.content == "ok"
    assert (
        "".join(c.content for c in llm_mod.stream_with_tools("hi", [dummy_tool]))
        == "hello"
    )


def test_invoke_chat_and_stream_chat():
    from backend.LLM.client.llm import invoke_chat, stream_chat

    class R:
        def invoke(self, inputs, config=None):
            return f"inv:{inputs}"

        def stream(self, inputs, config=None):
            yield "a"
            yield "b"

    assert invoke_chat(R(), "q") == "inv:q"
    assert list(stream_chat(R(), "q")) == ["a", "b"]
