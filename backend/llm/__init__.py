"""LLM 协作门面：其他后端只从这里 import。

打断相关：问卷由 ``ask`` 直接返回 ``AskInterruptResult``；
另仅暴露 ``submit_ask_interrupt``（无独立 create）。
"""

from backend.llm.graph import (
    AskStream,
    ask,
    delete_all_insights,
    delete_ask_histories_by_uuid,
    delete_ask_history,
    delete_section_insight,
    delete_user_insight,
    get_ask_history,
    get_section_facts,
    get_section_ids,
    get_section_insight,
    get_section_review,
    get_user_insight,
    load_section_document,
    release_ask_session,
    release_ask_sessions_by_uuid,
    set_section_review,
    submit_ask_interrupt,
    update_section_facts,
    update_section_insight_attrs,
    update_user_insight_attrs,
)
from backend.llm.schemas import (
    AskHistory,
    AskInterruptAnswerItem,
    AskInterruptResult,
    AskInterruptSubmitParams,
    AskParams,
    AskResult,
    DeleteHistoryResult,
    HistoryMessage,
    RagSnippet,
)

__all__ = [
    # —— 数据结构 ——
    "AskParams",
    "AskResult",
    "AskStream",
    "AskInterruptResult",
    "AskInterruptSubmitParams",
    "AskInterruptAnswerItem",
    "AskHistory",
    "HistoryMessage",
    "RagSnippet",
    "DeleteHistoryResult",
    # —— 对话 / 历史 / 释放 ——
    "ask",
    "submit_ask_interrupt",
    "get_section_ids",
    "get_ask_history",
    "delete_ask_history",
    "delete_ask_histories_by_uuid",
    "release_ask_session",
    "release_ask_sessions_by_uuid",
    # —— 用户 / 会话洞察 ——
    "get_user_insight",
    "update_user_insight_attrs",
    "delete_user_insight",
    "delete_all_insights",
    "get_section_insight",
    "update_section_insight_attrs",
    "delete_section_insight",
    # —— facts / review / 文档 ——
    "get_section_facts",
    "update_section_facts",
    "get_section_review",
    "set_section_review",
    "load_section_document",
]
