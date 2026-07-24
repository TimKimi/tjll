"""LLM 客户端单元测试（mock ChatOpenAI）。"""

from __future__ import annotations


class _FakeLLM:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.tools = None

    def bind_tools(self, tools):
        self.tools = list(tools)
        return self


def test_get_llm_passes_settings(monkeypatch):
    import backend.llm.client.llm as llm_mod

    captured = {}

    def fake_chat_openai(**kwargs):
        captured.update(kwargs)
        return _FakeLLM(**kwargs)

    monkeypatch.setattr(llm_mod, "ChatOpenAI", fake_chat_openai)
    llm = llm_mod.get_llm(temperature=0.2)
    assert captured["temperature"] == 0.2
    assert captured["model"] == llm_mod.settings.llm_model
    assert isinstance(llm, _FakeLLM)


def test_get_llm_with_tools(monkeypatch):
    import backend.llm.client.llm as llm_mod

    fake = _FakeLLM()
    monkeypatch.setattr(llm_mod, "get_llm", lambda temperature=0.2: fake)

    def dummy_tool(x: int) -> int:
        """add one"""
        return x + 1

    bound = llm_mod.get_llm_with_tools([dummy_tool])
    assert getattr(bound, "tools") == [dummy_tool]
