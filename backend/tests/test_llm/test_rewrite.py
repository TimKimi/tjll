"""查询重述单元测试（mock LLM，不依赖外部服务）。"""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def test_has_history_empty():
    from backend.llm.rephrase.rewrite import has_history

    assert has_history([]) is False
    assert has_history(None) is False


def test_has_history_with_messages():
    from backend.llm.rephrase.rewrite import has_history

    assert has_history([HumanMessage(content="你好")]) is True
    assert has_history([AIMessage(content="嗨")]) is True


def test_needs_rewrite_rules():
    from backend.llm.rephrase.rewrite import needs_rewrite

    assert needs_rewrite([], insight=None, attachment=None) is False
    assert needs_rewrite([], insight=[], attachment=[]) is False
    assert needs_rewrite([], insight=["属性"], attachment=None) is True
    assert needs_rewrite([], insight=None, attachment=["文档"]) is True
    assert (
        needs_rewrite(
            [HumanMessage(content="hi")],
            insight=None,
            attachment=None,
        )
        is True
    )


def test_rewrite_query_skips_first_turn_empty():
    from backend.llm.rephrase.rewrite import rewrite_query

    q = "王者荣耀英雄称号怎么分类？"
    assert rewrite_query(q, []) == q
    assert rewrite_query(q, None) == q


def test_rewrite_query_first_turn_with_insight(monkeypatch):
    from backend.llm.rephrase import rewrite as rewrite_mod

    class FakeChain:
        def invoke(self, inputs):
            assert "属性A" in inputs["insight_block"]
            assert inputs["attachment_block"] == "（无）"
            return "清洗后的检索查询含属性"

    monkeypatch.setattr(rewrite_mod, "build_rephrase_chain", lambda: FakeChain())
    out = rewrite_mod.rewrite_query("问题", [], insight=["属性A"])
    assert out == "清洗后的检索查询含属性"


def test_rewrite_query_first_turn_with_attachment(monkeypatch):
    from backend.llm.rephrase import rewrite as rewrite_mod

    class FakeChain:
        def invoke(self, inputs):
            assert "文档片段" in inputs["attachment_block"]
            return "含文档的检索查询"

    monkeypatch.setattr(rewrite_mod, "build_rephrase_chain", lambda: FakeChain())
    out = rewrite_mod.rewrite_query("问题", [], attachment=["文档片段"])
    assert out == "含文档的检索查询"


def test_rewrite_query_with_history(monkeypatch):
    from backend.llm.rephrase import rewrite as rewrite_mod

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
