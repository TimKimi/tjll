"""查询重述：首轮跳过，有历史时改写检索 query。"""

from __future__ import annotations

from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser

from backend.config import settings
from backend.llm.client.llm import get_llm
from backend.llm.prompts.rephrase import REPHRASE_PROMPT


def has_history(history: Sequence[BaseMessage] | None) -> bool:
    """是否存在可用于重述的 Human/AI 历史。"""
    if not history:
        return False
    return any(isinstance(m, (HumanMessage, AIMessage)) for m in history)


def build_rephrase_chain():
    """查询重述子链：temperature=settings.llm_rewrite_temperature。"""
    llm = get_llm(temperature=settings.llm_rewrite_temperature)
    return REPHRASE_PROMPT | llm | StrOutputParser()


def rewrite_query(query: str, history: Sequence[BaseMessage] | None) -> str:
    """首轮跳过重述；有历史时结合上下文改写检索 query。"""
    if not has_history(history):
        return query
    rephrase = build_rephrase_chain()
    rewritten = rephrase.invoke(
        {"query": query, "history": list(history or [])}
    ).strip()
    return rewritten or query
