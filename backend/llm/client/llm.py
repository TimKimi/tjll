"""LLM 基础封装：创建实例 / 工具绑定。"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from backend.config import settings

_MessageLike = str | BaseMessage | tuple[str, str] | dict[str, Any]


def get_llm(temperature: float = settings.llm_generate_temperature) -> ChatOpenAI:
    """创建 ChatOpenAI 实例；默认 temperature=settings.llm_generate_temperature。"""
    return ChatOpenAI(
        api_key=cast(Any, settings.api_key),
        base_url=settings.base_url,
        model=settings.llm_model,
        temperature=temperature,
        timeout=settings.llm_timeout,
        max_retries=settings.llm_max_retries,
    )


def _normalize_messages(messages: Sequence[_MessageLike] | str) -> list[BaseMessage]:
    if isinstance(messages, str):
        return [HumanMessage(content=messages)]

    out: list[BaseMessage] = []
    for m in messages:
        if isinstance(m, BaseMessage):
            out.append(m)
        elif isinstance(m, str):
            out.append(HumanMessage(content=m))
        elif isinstance(m, tuple) and len(m) == 2:
            role, content = m
            role_l = str(role).lower()
            if role_l in ("system", "sys"):
                out.append(SystemMessage(content=content))
            elif role_l in ("ai", "assistant"):
                out.append(AIMessage(content=content))
            else:
                out.append(HumanMessage(content=content))
        elif isinstance(m, dict):
            role = str(m.get("role", "user")).lower()
            content = str(m.get("content", ""))
            if role in ("system", "sys"):
                out.append(SystemMessage(content=content))
            elif role in ("assistant", "ai"):
                out.append(AIMessage(content=content))
            else:
                out.append(HumanMessage(content=content))
        else:
            raise TypeError(f"Unsupported message type: {type(m)!r}")
    return out


def _message_text(msg: Any) -> str:
    content = getattr(msg, "content", msg)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def get_llm_with_tools(
    tools: Sequence[Any],
    *,
    temperature: float = settings.llm_generate_temperature,
) -> Any:
    """绑定工具的 LLM（``bind_tools``）；不做多步 Agent loop。"""
    return get_llm(temperature=temperature).bind_tools(list(tools))
