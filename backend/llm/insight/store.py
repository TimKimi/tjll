"""UserInsight / SectionInsight 的 Redis 持久化。"""

from __future__ import annotations

import json
import logging
from typing import Any

from redis import Redis

from backend.config import settings
from backend.llm.insight.model import UserInsight
from backend.llm.insight.section import SectionInsight

logger = logging.getLogger("backend.llm.insight.store")

_USER_KEY = "insight:user:{uuid}"
_SECTION_KEY = "insight:section:{uuid}::{section_id}"


def _client() -> Any:
    return Redis.from_url(settings.redis_url)


def user_insight_key(uuid: str) -> str:
    return _USER_KEY.format(uuid=(uuid or "").strip())


def section_insight_key(uuid: str, section_id: str) -> str:
    return _SECTION_KEY.format(
        uuid=(uuid or "").strip(),
        section_id=(section_id or "").strip(),
    )


def save_user_insight(insight: UserInsight) -> None:
    """将用户洞察写入 Redis。"""
    key = user_insight_key(insight.uuid)
    attrs = insight.as_dict()
    payload: dict[str, Any] = {
        "uuid": insight.uuid,
        "attrs": attrs,
        "last_chunk_size": int(insight.last_chunk_size),
        "max_attr_len": int(insight.max_attr_len),
    }
    try:
        client = _client()
        try:
            client.set(
                key,
                json.dumps(payload, ensure_ascii=False),
                ex=settings.redis_history_ttl,
            )
            logger.info("save_user_insight key=%s attrs=%d", key, len(attrs))
        finally:
            try:
                client.close()
            except Exception:
                pass
    except Exception:
        logger.exception("save_user_insight redis failed key=%s", key)


def load_user_insight(uuid: str) -> UserInsight | None:
    """从 Redis 加载用户洞察；不存在或连接失败返回 None。"""
    uuid = (uuid or "").strip()
    if not uuid:
        raise ValueError("uuid is required")
    key = user_insight_key(uuid)
    try:
        client = _client()
        try:
            raw = client.get(key)
        finally:
            try:
                client.close()
            except Exception:
                pass
    except Exception:
        logger.exception("load_user_insight redis failed key=%s", key)
        return None
    if not raw:
        return None
    text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
    data = json.loads(text)
    insight = UserInsight(uuid)
    attrs = data.get("attrs") or {}
    if isinstance(attrs, dict) and attrs:
        insight.batch_add(attrs)
    insight.last_chunk_size = int(data.get("last_chunk_size") or 0)
    insight.max_attr_len = int(data.get("max_attr_len") or insight.max_attr_len)
    logger.info("load_user_insight key=%s attrs=%d", key, len(insight._attrs))
    return insight


def save_section_insight(section: SectionInsight) -> None:
    """将会话洞察写入 Redis（不含父类 attrs）。"""
    key = section_insight_key(section.uuid, section.section_id)
    filenames = section.filenames()
    used_filenames = section.used_filenames()
    payload: dict[str, Any] = {
        "uuid": section.uuid,
        "section_id": section.section_id,
        "section_attrs": section.section_as_dict(),
        "filenames": filenames,
        "used_filenames": used_filenames,
        "facts": section.get_facts(),
        "review": section.get_review(),
        "last_section_chunk_size": int(section.last_section_chunk_size),
        "max_section_attr_len": int(section.max_section_attr_len),
    }
    try:
        client = _client()
        try:
            client.set(
                key,
                json.dumps(payload, ensure_ascii=False),
                ex=settings.redis_history_ttl,
            )
            logger.info(
                "save_section_insight key=%s files=%d used=%d",
                key,
                len(filenames),
                len(used_filenames),
            )
        finally:
            try:
                client.close()
            except Exception:
                pass
    except Exception:
        logger.exception("save_section_insight redis failed key=%s", key)


def load_section_insight(
    uuid: str,
    section_id: str,
    *,
    parent: UserInsight,
) -> SectionInsight | None:
    """从 Redis 加载会话洞察并挂到 parent；不存在或连接失败返回 None。"""
    uuid = (uuid or "").strip()
    section_id = (section_id or "").strip()
    if not uuid or not section_id:
        raise ValueError("uuid and section_id are required")
    key = section_insight_key(uuid, section_id)
    try:
        client = _client()
        try:
            raw = client.get(key)
        finally:
            try:
                client.close()
            except Exception:
                pass
    except Exception:
        logger.exception("load_section_insight redis failed key=%s", key)
        return None
    if not raw:
        return None
    text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
    data = json.loads(text)
    section = SectionInsight(uuid, section_id, parent=parent)
    section_attrs = data.get("section_attrs") or {}
    if isinstance(section_attrs, dict) and section_attrs:
        section.batch_add_section(section_attrs)
    section._filenames = [str(x) for x in (data.get("filenames") or [])]
    section._used_filenames = [str(x) for x in (data.get("used_filenames") or [])]
    section._facts = [str(x) for x in (data.get("facts") or [])]
    section._review = str(data.get("review") or "")
    section.last_section_chunk_size = int(data.get("last_section_chunk_size") or 0)
    section.max_section_attr_len = int(
        data.get("max_section_attr_len") or section.max_section_attr_len
    )
    logger.info(
        "load_section_insight key=%s files=%d used=%d",
        key,
        len(section._filenames),
        len(section._used_filenames),
    )
    return section
