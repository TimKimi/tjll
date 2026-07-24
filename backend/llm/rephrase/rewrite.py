"""查询重述：可跳过；否则 tool_loop（review/facts/打断/finish）。"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from backend.config import settings
from backend.llm.client.tool_loop import run_tool_loop
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
    """查询重述子链：temperature=settings.llm_rewrite_temperature（无工具路径）。"""
    from langchain_core.output_parsers import StrOutputParser

    from backend.llm.client.llm import get_llm

    llm = get_llm(temperature=settings.llm_rewrite_temperature)
    return REPHRASE_PROMPT | llm | StrOutputParser()


def rewrite_query(
    query: str,
    history: Sequence[BaseMessage] | None,
    *,
    insight: Sequence[str] | None = None,
    attachment: Sequence[str] | None = None,
) -> str:
    """合成检索用 search_query；跳过条件与 needs_rewrite 一致（无工具旧路径）。"""
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


def _format_interrupt_qa(items: Sequence[dict[str, Any]] | None) -> str:
    if not items:
        return "（无）"
    lines: list[str] = []
    for item in items:
        q = str(item.get("question") or "").strip()
        if not q:
            continue
        if "result" in item and str(item.get("result") or "").strip():
            lines.append(f"- Q: {q}\n  A: {item.get('result')}")
        else:
            raw_opt = item.get("option")
            option: dict[Any, Any] = raw_opt if isinstance(raw_opt, dict) else {}
            opt_txt = ", ".join(f"{k}={v}" for k, v in option.items())
            lines.append(f"- Q: {q}\n  options: {opt_txt or '（空）'}")
    return "\n".join(lines) if lines else "（无）"


def rewrite_query_with_tools(
    query: str,
    history: Sequence[BaseMessage] | None,
    *,
    section: Any,
    insight: Sequence[str] | None = None,
    attachment: Sequence[str] | None = None,
    force: bool = False,
) -> tuple[str, str]:
    """工具改写：可读 review/facts；可打断；产出 (search_query, detail)。

    已有 interrupt 答案时禁止再打断。调用 ask_user_interrupt 会抛 AskInterruptSignal。
    ``force`` 保留兼容；进入本函数即走工具循环（不再因首轮跳过）。
    """
    _ = force
    insight_list = _nonempty_texts(insight)
    attachment_list = _nonempty_texts(attachment)

    insight_block = (
        _format_block("相关属性", insight_list) if insight_list else "（无）"
    )
    attachment_block = (
        _format_block("相关文档", attachment_list) if attachment_list else "（无）"
    )
    qa_block = _format_interrupt_qa(section.get_interrupt_qa())
    has_answers = section.has_interrupt_answers()

    system = (
        "你负责把用户最新问题改写成检索查询，并可补充 detail。\n"
        "可调用 get_section_review / get_section_facts 查阅会话摘要与事实。\n"
        "信息足够、检索意图清晰时必须调用 finish_rewrite(search_query, detail)：\n"
        "- search_query：独立完整的中文检索文本；\n"
        "- detail：有利于最终回答的补充信息（可空）。\n"
    )
    if has_answers:
        system += (
            "用户已回答澄清题（见下方问答），请结合答案改写；"
            "禁止再调用 ask_user_interrupt。\n"
        )
    else:
        system += (
            "若现有属性/文档/历史仍模糊，或缺少关键约束会导致后续资料检索不准，"
            "必须调用 ask_user_interrupt 发起一批多选题（option 用 A/B/C… 键，"
            "最后一项可为「其他」）；调用后本轮暂停，等待用户作答。\n"
            "仅当问题本身已足够支撑精准检索时，才直接 finish_rewrite，不要打断。\n"
        )

    human = (
        f"最新问题：{query}\n\n"
        f"{insight_block}\n\n"
        f"{attachment_block}\n\n"
        f"澄清问答：\n{qa_block}\n\n"
        "请查阅工具（如需）后：信息不够则 ask_user_interrupt；"
        "足够则 finish_rewrite。"
    )
    messages: list[BaseMessage] = [SystemMessage(content=system)]
    messages.extend(list(history or []))
    messages.append(HumanMessage(content=human))

    holder: dict[str, str] = {"search_query": "", "detail": ""}
    tools = [
        section.as_get_review_tool(),
        section.as_get_facts_tool(),
        section.as_finish_rewrite_tool(holder),
    ]
    if not has_answers:
        tools.append(section.as_ask_user_interrupt_tool())

    run_tool_loop(
        messages,
        tools,
        temperature=settings.llm_rewrite_temperature,
        max_rounds=6,
    )
    search_query = holder["search_query"].strip() or query
    detail = holder["detail"].strip()
    logger.info(
        "rewrite_with_tools before=%r after=%r detail_len=%d",
        query,
        search_query,
        len(detail),
    )
    return search_query, detail
