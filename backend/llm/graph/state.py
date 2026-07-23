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
    history: list[BaseMessage]
    insight_use: bool  # 是否检索用户级洞察属性
    search_query: str
    context: str  # 参考资料（RAG 检索结果）
    answer: str
    insight: list[str]  # 用户/会话属性片段
    attachment: list[str]  # 本轮附件文档 chunk
    attachment_filenames: list[str]  # 本轮附件路径（边检测用）
