"""Ask 图 State（TypedDict）。"""

from __future__ import annotations

from typing import TypedDict

from langchain_core.messages import BaseMessage


class AskState(TypedDict, total=False):
    """一轮图执行状态。

    ``sources`` 不进 State，由 retrieve 节点调用工具后写入 AskSession 侧车。
    ``history`` 为会话内存中的消息（释放池槽时才刷 Redis）。
    """

    query: str
    section_id: str
    uuid: str
    insight_create: bool
    insight_use: bool
    history: list[BaseMessage]
    search_query: str
    context: str
    answer: str
