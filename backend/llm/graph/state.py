"""Ask 图 State（TypedDict）。"""

from __future__ import annotations

from typing import TypedDict


class AskState(TypedDict, total=False):
    """一轮图执行状态。

    ``sources`` / ``history`` 不进 State：分别写在 AskSession 侧车与
    ``AskSession.history``（释放池槽时才刷 Redis）。
    """

    query: str
    section_id: str
    uuid: str
    insight_use: bool  # 是否检索用户级洞察属性
    search_query: str
    context: str  # 参考资料（RAG 检索结果）
    answer: str
    insight: list[str]  # 用户/会话属性片段
    attachment: list[str]  # 本轮附件文档 chunk
    attachment_filenames: list[str]  # 本轮附件路径（边检测用）
