"""会话历史窗口：过滤 system、按 used 装载。"""

from __future__ import annotations

from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from backend.llm.session.history import get_history

CompleteTurn = tuple[HumanMessage, AIMessage]


def filter_chat_messages(messages: Sequence[BaseMessage]) -> list[BaseMessage]:
    """丢弃 SystemMessage，仅保留 Human/AI。"""
    return [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]


def _msg_used(msg: BaseMessage) -> bool:
    extra = getattr(msg, "additional_kwargs", None) or {}
    return bool(extra.get("used", False))


def iter_complete_turns(messages: Sequence[BaseMessage]) -> list[CompleteTurn]:
    """按顺序提取完整 user+assistant 轮。"""
    turns: list[CompleteTurn] = []
    i = 0
    msgs = list(messages)
    while i < len(msgs) - 1:
        a, b = msgs[i], msgs[i + 1]
        if isinstance(a, HumanMessage) and isinstance(b, AIMessage):
            turns.append((a, b))
            i += 2
            continue
        i += 1
    return turns


def select_history_window(
    messages: Sequence[BaseMessage],
    *,
    min_turns: int = 3,
) -> list[BaseMessage]:
    """从消息列表选内存窗口：尾部 used=false；不足 min_turns 则向上补。"""
    msgs = filter_chat_messages(messages)
    turns = iter_complete_turns(msgs)
    if not turns:
        return []

    unused_from_end: list[CompleteTurn] = []
    for turn in reversed(turns):
        if _msg_used(turn[0]) or _msg_used(turn[1]):
            break
        unused_from_end.append(turn)
    unused_from_end.reverse()

    selected = list(unused_from_end)
    if len(selected) < min_turns:
        need = min_turns - len(selected)
        earlier = turns[: len(turns) - len(unused_from_end)]
        pad = earlier[-need:] if need <= len(earlier) else earlier
        selected = list(pad) + selected

    out: list[BaseMessage] = []
    for human, ai in selected:
        out.append(human)
        out.append(ai)
    return out


def load_history_window_from_redis(
    uuid: str,
    section_id: str,
    *,
    min_turns: int = 3,
) -> list[BaseMessage]:
    """从 Redis 装内存窗口：尾部 used=false；不足 min_turns 则向上补。"""
    raw = list(get_history(uuid, section_id).messages)
    return select_history_window(raw, min_turns=min_turns)
