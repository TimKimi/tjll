"""查询重述：首轮且无洞察/附件时跳过；否则改写并清洗进 search_query。"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser

from backend.config import settings
from backend.llm.client.llm import get_llm
from backend.llm.prompts.rephrase import REPHRASE_PROMPT

logger = logging.getLogger("backend.llm.rephrase.rewrite")


def has_history(history: Sequence[BaseMessage] | None) -> bool:
    """是否存在可用于重述的 Human/AI 历史。"""
    if not history:
        return False
    return any(isinstance(m, (HumanMessage, AIMessage)) for m in history)


def _nonempty_texts(items: Sequence[str] | None) -> list[str]:
    if not items:
        return []
    return [str(x).strip() for x in items if str(x).strip()]


def needs_rewrite(
    history: Sequence[BaseMessage] | None,
    *,
    insight: Sequence[str] | None = None,
    attachment: Sequence[str] | None = None,
) -> bool:
    """insight 非空 或 attachment 非空 或 非首轮 → 需要改写。"""
    if has_history(history):
        return True
    if _nonempty_texts(insight):
        return True
    if _nonempty_texts(attachment):
        return True
    return False


def _format_block(title: str, items: Sequence[str]) -> str:
    lines = [f"- {t}" for t in items]
    return f"{title}:\n" + "\n".join(lines)


def build_rephrase_chain():
    """查询重述子链：temperature=settings.llm_rewrite_temperature。"""
    llm = get_llm(temperature=settings.llm_rewrite_temperature)
    return REPHRASE_PROMPT | llm | StrOutputParser()


def rewrite_query(
    query: str,
    history: Sequence[BaseMessage] | None,
    *,
    insight: Sequence[str] | None = None,
    attachment: Sequence[str] | None = None,
) -> str:
    """合成检索用 search_query；跳过条件与 needs_rewrite 一致。"""
    insight_list = _nonempty_texts(insight)
    attachment_list = _nonempty_texts(attachment)
    if not needs_rewrite(history, insight=insight_list, attachment=attachment_list):
        logger.info(
            "rewrite skipped (first turn, no insight/attachment) query=%r", query
        )
        return query

    insight_block = (
        _format_block("相关属性", insight_list) if insight_list else "（无）"
    )
    attachment_block = (
        _format_block("相关文档", attachment_list) if attachment_list else "（无）"
    )
    rephrase = build_rephrase_chain()
    rewritten = rephrase.invoke(
        {
            "query": query,
            "history": list(history or []),
            "insight_block": insight_block,
            "attachment_block": attachment_block,
        }
    ).strip()
    out = rewritten or query
    logger.info("rewrite before=%r after=%r", query, out)
    return out
