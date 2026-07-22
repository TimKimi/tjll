"""Redis 对话历史。"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_redis import RedisChatMessageHistory
from redis import Redis

from backend.config import settings

logger = logging.getLogger("backend.llm.session.history")

_CHAT_KEY_PREFIX = "chat:"


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


def clear_history(uuid: str, section_id: str) -> None:
    """删除单个会话的 Redis 聊天历史。"""
    hist = get_history(uuid, section_id)
    hist.clear()
    logger.info(
        "clear_history uuid=%s section_id=%s",
        uuid.strip(),
        section_id.strip(),
    )


def list_history_session_ids_for_uuid(uuid: str) -> list[str]:
    """扫描 Redis，列出该 uuid 下所有 ``uuid::section_id`` 会话 id。"""
    uuid = _require_id("uuid", uuid)
    client: Any = Redis.from_url(settings.redis_url)
    pattern = f"{_CHAT_KEY_PREFIX}{uuid}::*"
    session_ids: set[str] = set()
    try:
        for raw in client.scan_iter(match=pattern, count=200):
            text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
            if not text.startswith(_CHAT_KEY_PREFIX):
                continue
            rest = text[len(_CHAT_KEY_PREFIX) :]
            session_id, sep, _msgid = rest.rpartition(":")
            if not sep or not session_id.startswith(f"{uuid}::"):
                continue
            session_ids.add(session_id)
    finally:
        try:
            client.close()
        except Exception:
            pass
    return sorted(session_ids)


def clear_histories_for_uuid(uuid: str) -> list[str]:
    """删除该 uuid 下全部会话的 Redis 聊天历史；返回已清理的 session_id 列表。"""
    uuid = _require_id("uuid", uuid)
    session_ids = list_history_session_ids_for_uuid(uuid)
    cleared: list[str] = []
    for session_id in session_ids:
        parts = session_id.split("::", 1)
        if len(parts) != 2:
            continue
        get_history(parts[0], parts[1]).clear()
        cleared.append(session_id)
    logger.info("clear_histories_for_uuid uuid=%s sessions=%d", uuid, len(cleared))
    return cleared
