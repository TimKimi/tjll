"""带工具的简单多轮调用（维护节点用）。"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool

from backend.llm.client.llm import (
    get_llm_with_tools,
    _message_text,
    _normalize_messages,
)

logger = logging.getLogger("backend.llm.client.tool_loop")


def run_tool_loop(
    messages: Sequence[Any],
    tools: Sequence[BaseTool],
    *,
    temperature: float,
    max_rounds: int = 6,
) -> AIMessage:
    """绑定 tools 后循环执行 tool_calls，直到无调用或达上限。"""
    llm = get_llm_with_tools(tools, temperature=temperature)
    tool_map = {t.name: t for t in tools}
    msgs: list[BaseMessage] = list(_normalize_messages(messages))
    last: AIMessage = AIMessage(content="")
    for _ in range(max_rounds):
        result = llm.invoke(msgs)
        if isinstance(result, AIMessage):
            last = result
        else:
            last = AIMessage(content=_message_text(result))
        calls = getattr(last, "tool_calls", None) or []
        if not calls:
            return last
        msgs.append(last)
        for call in calls:
            name = str(call.get("name") or "")
            call_id = str(call.get("id") or name)
            args = call.get("args") or {}
            tool = tool_map.get(name)
            if tool is None:
                content = f"unknown tool: {name}"
            else:
                try:
                    out = tool.invoke(args)
                    content = (
                        out
                        if isinstance(out, str)
                        else json.dumps(out, ensure_ascii=False, default=str)
                    )
                except Exception as exc:
                    logger.exception("tool %s failed", name)
                    content = f"error: {exc}"
            msgs.append(ToolMessage(content=str(content), tool_call_id=call_id))
    return last
