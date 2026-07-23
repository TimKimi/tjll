"""UserInsight / SectionInsight 进程内单例注册表（共享父实例）。"""

from __future__ import annotations

import logging
import threading

from backend.llm.insight.model import UserInsight
from backend.llm.insight.section import SectionInsight
from backend.llm.session.history import make_history_session_id

logger = logging.getLogger("backend.llm.insight.registry")


def _require_id(name: str, value: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


class InsightRegistry:
    """uuid → UserInsight；uuid::section_id → SectionInsight（共享父实例）。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._users: dict[str, UserInsight] = {}
        self._sections: dict[str, SectionInsight] = {}

    def ensure_user_insight(self, uuid: str) -> UserInsight:
        """内存 → Redis → 新建。"""
        uuid = _require_id("uuid", uuid)
        with self._lock:
            insight = self._users.get(uuid)
            if insight is not None:
                return insight
        loaded = UserInsight.load_from_redis(uuid)
        with self._lock:
            existing = self._users.get(uuid)
            if existing is not None:
                return existing
            if loaded is not None:
                self._users[uuid] = loaded
                logger.info("user_insight restore uuid=%s", uuid)
                return loaded
            insight = UserInsight(uuid)
            self._users[uuid] = insight
            logger.info("user_insight create uuid=%s", uuid)
            return insight

    def ensure_section_insight(self, uuid: str, section_id: str) -> SectionInsight:
        """内存 → Redis（挂共享 parent）→ 新建。"""
        uuid = _require_id("uuid", uuid)
        section_id = _require_id("section_id", section_id)
        key = make_history_session_id(uuid, section_id)
        with self._lock:
            section = self._sections.get(key)
            if section is not None:
                return section
        parent = self.ensure_user_insight(uuid)
        loaded = SectionInsight.load_section_from_redis(uuid, section_id, parent=parent)
        with self._lock:
            existing = self._sections.get(key)
            if existing is not None:
                return existing
            if loaded is not None:
                # 保证挂到当前内存 parent（可能与 load 时 parent 不同实例）
                loaded._parent = parent
                self._sections[key] = loaded
                logger.info("section_insight restore key=%s", key)
                return loaded
            section = SectionInsight(uuid, section_id, parent=parent)
            self._sections[key] = section
            logger.info("section_insight create key=%s", key)
            return section

    def drop_section_insight(self, uuid: str, section_id: str) -> bool:
        """移除会话洞察；若该 uuid 无剩余 section 则释放内存 UserInsight。"""
        uuid = _require_id("uuid", uuid)
        section_id = _require_id("section_id", section_id)
        key = make_history_session_id(uuid, section_id)
        with self._lock:
            removed = self._sections.pop(key, None) is not None
            if removed:
                logger.info("section_insight drop key=%s", key)
                prefix = f"{uuid}::"
                still = any(k.startswith(prefix) for k in self._sections)
                if not still and uuid in self._users:
                    self._users.pop(uuid, None)
                    logger.info("user_insight drop uuid=%s (no sections left)", uuid)
        return removed

    def peek_section_insight(self, uuid: str, section_id: str) -> SectionInsight | None:
        """若已存在则返回，不创建。"""
        key = make_history_session_id(
            _require_id("uuid", uuid),
            _require_id("section_id", section_id),
        )
        with self._lock:
            return self._sections.get(key)

    def peek_user_insight(self, uuid: str) -> UserInsight | None:
        with self._lock:
            return self._users.get(_require_id("uuid", uuid))

    def drop_sections_for_uuid(self, uuid: str) -> list[str]:
        uuid = _require_id("uuid", uuid)
        prefix = f"{uuid}::"
        with self._lock:
            keys = [k for k in self._sections if k.startswith(prefix)]
            for key in keys:
                self._sections.pop(key, None)
            if uuid in self._users:
                self._users.pop(uuid, None)
                logger.info("user_insight drop uuid=%s (all sections)", uuid)
        if keys:
            logger.info("section_insight drop uuid=%s count=%d", uuid, len(keys))
        return keys

    def reset(self) -> None:
        """测试用：清空全部单例。"""
        with self._lock:
            self._users.clear()
            self._sections.clear()


_registry = InsightRegistry()


def get_insight_registry() -> InsightRegistry:
    return _registry


def ensure_user_insight(uuid: str) -> UserInsight:
    return _registry.ensure_user_insight(uuid)


def ensure_section_insight(uuid: str, section_id: str) -> SectionInsight:
    return _registry.ensure_section_insight(uuid, section_id)


def drop_section_insight(uuid: str, section_id: str) -> bool:
    return _registry.drop_section_insight(uuid, section_id)
