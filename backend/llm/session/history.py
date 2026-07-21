"""Redis 对话历史。"""

from __future__ import annotations

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_redis import RedisChatMessageHistory

from backend.config import settings


def _require_id(name: str, value: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


def make_history_session_id(uuid: str, section_id: str) -> str:
    """历史 Redis key：必须同时有 uuid 与 section_id。"""
    return f"{_require_id('uuid', uuid)}::{_require_id('section_id', section_id)}"


def get_history(uuid: str, section_id: str) -> BaseChatMessageHistory:
    """按 ``uuid`` + ``section_id`` 获取 Redis 会话历史（二者均必填）。"""
    return RedisChatMessageHistory(
        session_id=make_history_session_id(uuid, section_id),
        redis_url=settings.redis_url,
        ttl=settings.redis_history_ttl,
    )


def get_history_by_session_key(session_id: str) -> BaseChatMessageHistory:
    """供 LCEL ``RunnableWithMessageHistory``：session_id 必须为 ``uuid::section_id``。"""
    parts = (session_id or "").split("::", 1)
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        raise ValueError(
            "session_id must be '{uuid}::{section_id}' with both parts non-empty"
        )
    return get_history(parts[0].strip(), parts[1].strip())
