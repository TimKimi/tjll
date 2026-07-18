"""LLM 基础封装：非流式 / 流式 / 工具绑定。"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any, cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
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


def invoke_llm(
    messages: Sequence[_MessageLike] | str,
    *,
    temperature: float = settings.llm_generate_temperature,
    **kwargs: Any,
) -> str:
    """非流式调用，返回文本。"""
    llm = get_llm(temperature=temperature)
    result = llm.invoke(_normalize_messages(messages), **kwargs)
    return _message_text(result)


def stream_llm(
    messages: Sequence[_MessageLike] | str,
    *,
    temperature: float = settings.llm_generate_temperature,
    **kwargs: Any,
) -> Iterator[str]:
    """流式调用，逐 token 产出文本片段。"""
    llm = get_llm(temperature=temperature)
    for chunk in llm.stream(_normalize_messages(messages), **kwargs):
        text = _message_text(chunk)
        if text:
            yield text


def invoke_chat(
    runnable: Any,
    inputs: Any,
    config: RunnableConfig | None = None,
) -> Any:
    """LCEL Runnable 非流式调用。"""
    return runnable.invoke(inputs, config=config)


def stream_chat(
    runnable: Any,
    inputs: Any,
    config: RunnableConfig | None = None,
) -> Iterator[Any]:
    """LCEL Runnable 流式调用。"""
    yield from runnable.stream(inputs, config=config)


def get_llm_with_tools(
    tools: Sequence[Any],
    *,
    temperature: float = settings.llm_generate_temperature,
) -> Any:
    """绑定工具的 LLM（``bind_tools``）；不做多步 Agent loop。"""
    return get_llm(temperature=temperature).bind_tools(list(tools))


def invoke_with_tools(
    messages: Sequence[_MessageLike] | str,
    tools: Sequence[Any],
    *,
    temperature: float = settings.llm_generate_temperature,
    **kwargs: Any,
) -> AIMessage:
    """带工具绑定的非流式调用，返回完整 AIMessage（可能含 tool_calls）。"""
    llm = get_llm_with_tools(tools, temperature=temperature)
    result = llm.invoke(_normalize_messages(messages), **kwargs)
    if isinstance(result, AIMessage):
        return result
    return AIMessage(content=_message_text(result))


def stream_with_tools(
    messages: Sequence[_MessageLike] | str,
    tools: Sequence[Any],
    *,
    temperature: float = settings.llm_generate_temperature,
    **kwargs: Any,
) -> Iterator[Any]:
    """带工具绑定的流式调用，产出原始 chunk。"""
    llm = get_llm_with_tools(tools, temperature=temperature)
    yield from llm.stream(_normalize_messages(messages), **kwargs)
