"""查询重述单元测试（mock LLM，不依赖外部服务）。"""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def test_has_history_empty():
    from backend.LLM.rephrase.rewrite import has_history

    assert has_history([]) is False
    assert has_history(None) is False


def test_has_history_with_messages():
    from backend.LLM.rephrase.rewrite import has_history

    assert has_history([HumanMessage(content="你好")]) is True
    assert has_history([AIMessage(content="嗨")]) is True


def test_rewrite_query_skips_first_turn():
    from backend.LLM.rephrase.rewrite import rewrite_query

    q = "王者荣耀英雄称号怎么分类？"
    assert rewrite_query(q, []) == q
    assert rewrite_query(q, None) == q


def test_rewrite_query_with_history(monkeypatch):
    from backend.LLM.rephrase import rewrite as rewrite_mod

    class FakeChain:
        def invoke(self, inputs):
            assert "history" in inputs
            return "王者荣耀英雄称号的符号学分类"

    monkeypatch.setattr(rewrite_mod, "build_rephrase_chain", lambda: FakeChain())

    history: list[BaseMessage] = [
        HumanMessage(content="王者荣耀英雄称号从哪些角度分类？"),
        AIMessage(content="可以从符号学等角度。"),
    ]
    out = rewrite_mod.rewrite_query("符号学角度具体怎么说？", history)
    assert out == "王者荣耀英雄称号的符号学分类"
