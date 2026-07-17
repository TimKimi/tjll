"""LLM prompts 轻量单元测试。"""

from __future__ import annotations

from langchain_core.messages import HumanMessage


def _message_text(msg: object) -> str:
    content = getattr(msg, "content", "")
    return content if isinstance(content, str) else ""


def test_rag_prompt_formats():
    from backend.LLM.prompts.rag import RAG_PROMPT, RAG_PROMPT_WITH_HISTORY

    msgs = RAG_PROMPT.format_messages(context="资料", query="问题")
    text = "\n".join(_message_text(m) for m in msgs)
    assert "资料" in text
    assert "问题" in text

    msgs2 = RAG_PROMPT_WITH_HISTORY.format_messages(
        context="上下文",
        query="追问",
        history=[HumanMessage(content="上一轮")],
    )
    joined = "\n".join(_message_text(m) for m in msgs2)
    assert "上下文" in joined
    assert "追问" in joined


def test_rephrase_prompt_formats():
    from backend.LLM.prompts.rephrase import REPHRASE_PROMPT

    msgs = REPHRASE_PROMPT.format_messages(
        query="这个怎么样",
        history=[HumanMessage(content="谈到餐厅")],
    )
    joined = "\n".join(_message_text(m) for m in msgs)
    assert "这个怎么样" in joined
    assert "改写后" in joined
