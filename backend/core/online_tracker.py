"""Token 过期自动同步 is_online。

启动时开启后台守护线程，定期检查记录中的 token 是否过期，
过期后将对应用户的 ``is_online`` 置为 ``false``。

使用方式::

    from backend.core.online_tracker import tracker

    # 登录成功时
    tracker.mark_online(user_id, expires_delta)

    # 主动登出时
    tracker.mark_offline(user_id)
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import timedelta
from typing import Any

from sqlalchemy import create_engine, text

from backend.config import settings

logger = logging.getLogger("backend.core.online_tracker")

# 异步 DATABASE_URL → 同步 URL（去掉 +asyncpg）
_SYNC_DB_URL = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


class _OnlineTracker:
    """追踪在线用户 token 过期时间，后台线程自动同步。

    服务重启时所有用户初始化为离线（清空 token 状态），
    用户登录后由 ``mark_online`` 重新追踪。
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # user_id -> 过期时间戳（UTC 秒）
        self._users: dict[str, float] = {}
        self._interval: int = settings.ONLINE_TRACKER_CHECK_INTERVAL
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._engine: Any = None

    def mark_online(self, user_id: str, expires_delta: timedelta) -> None:
        """记录用户上线及 token 过期时间。"""
        expiry = time.time() + expires_delta.total_seconds()
        with self._lock:
            self._users[user_id] = expiry

    def mark_offline(self, user_id: str) -> None:
        """用户主动登出，移除追踪记录。"""
        with self._lock:
            self._users.pop(user_id, None)

    def start(self) -> None:
        """启动后台守护线程。

        当 ``settings.ONLINE_TRACKER_RESET_ON_STARTUP = True`` 时，
        启动时将数据库中所有用户 ``is_online`` 置为 ``false``。
        """
        if self._thread is not None:
            return
        self._engine = create_engine(_SYNC_DB_URL, pool_pre_ping=True)
        if settings.ONLINE_TRACKER_RESET_ON_STARTUP:
            self._reset_all_online()
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(
            "online tracker started, interval=%ds, reset_on_startup=%s",
            self._interval,
            settings.ONLINE_TRACKER_RESET_ON_STARTUP,
        )

    def stop(self) -> None:
        """停止后台线程并将所有追踪用户置为离线。"""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._flush_all()
        if self._engine:
            self._engine.dispose()
        logger.info("online tracker stopped")

    # ── 内部 ─────────────────────────────────────────────

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            self._check_expired()

    def _check_expired(self) -> None:
        now = time.time()
        expired: list[str] = []
        with self._lock:
            for uid, exp in list(self._users.items()):
                if now >= exp:
                    expired.append(uid)
                    del self._users[uid]
        if expired:
            self._sync_offline(expired)

    def _sync_offline(self, user_ids: list[str]) -> None:
        """批量更新 DB is_online = false。"""
        if not self._engine:
            return
        try:
            with self._engine.connect() as conn:
                conn.execute(
                    text("UPDATE app_users SET is_online = false WHERE id = ANY(:ids)"),
                    {"ids": user_ids},
                )
                conn.commit()
            logger.info("synced offline %d users: %s", len(user_ids), user_ids)
        except Exception as e:
            logger.error("sync offline failed: %s", e)

    def _reset_all_online(self) -> None:
        """初始化：将所有用户置为离线，清空所有追踪记录。

        同时记录重置时间戳 ``_reset_iat``，在此时间之前签发的 JWT
        将在 ``get_current_user`` 中被拒绝（实现 token 失效）。
        """
        with self._lock:
            self._users.clear()
        self._reset_iat = time.time()
        if not self._engine:
            return
        try:
            with self._engine.connect() as conn:
                conn.execute(text("UPDATE app_users SET is_online = false"))
                conn.commit()
            logger.info(
                "reset all users to offline, tokens issued before %.0f invalidated",
                self._reset_iat,
            )
        except Exception as e:
            logger.error("reset all users offline failed: %s", e)

    @property
    def reset_iat(self) -> float:
        """获取重置时间戳。未重置时返回 0（不进行 iat 检查）。"""
        return getattr(self, "_reset_iat", 0.0)

    def _flush_all(self) -> None:
        with self._lock:
            ids = list(self._users.keys())
            self._users.clear()
        if ids:
            self._sync_offline(ids)


# 全局单例
tracker = _OnlineTracker()
