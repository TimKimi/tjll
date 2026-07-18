"""Redis 对话历史。"""

from __future__ import annotations

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_redis import RedisChatMessageHistory

from backend.config import settings


def get_history(section_id: str) -> BaseChatMessageHistory:
    """按 section_id 获取 Redis 会话历史。

    ``RunnableWithMessageHistory`` 默认 configurable 键为 ``session_id``；
    ``rag_pipeline`` 将外部 ``section_id`` 映射为 ``session_id`` 后传入。
    """
    return RedisChatMessageHistory(
        session_id=section_id,
        redis_url=settings.redis_url,
        ttl=settings.redis_history_ttl,
    )
