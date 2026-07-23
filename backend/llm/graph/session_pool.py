"""按 (uuid, section_id) 管理 Ask 会话：内存历史 + LRU 池（最多 5 个）。"""

from __future__ import annotations

import atexit
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from backend.llm.insight.registry import drop_section_insight
from backend.llm.insight.section import SectionInsight
from backend.llm.session.history import get_history, make_history_session_id

logger = logging.getLogger("backend.llm.graph.session_pool")

MAX_SESSIONS = 5
SESSION_IDLE_SECONDS = 120.0
_IDLE_SWEEP_INTERVAL = 30.0


def _require_id(name: str, value: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


@dataclass
class PendingTurn:
    """尚未刷入 Redis 的一轮问答（含扩展字段）。"""

    user: HumanMessage
    assistant: AIMessage


@dataclass
class AskSession:
    """单个会话槽：内存 history；释放/空闲时才刷 Redis。"""

    uuid: str
    section_id: str
    history: list[BaseMessage] = field(default_factory=list)
    pending_turns: list[PendingTurn] = field(default_factory=list)
    last_sources: list[dict[str, Any]] = field(default_factory=list)
    last_search_query: str = ""
    last_used: float = field(default_factory=time.monotonic)
    graph: Any | None = None
    section_insight: SectionInsight | None = None

    @property
    def key(self) -> str:
        return make_session_key(self.uuid, self.section_id)

    def touch(self) -> None:
        self.last_used = time.monotonic()

    def append_turn(
        self,
        user: str,
        assistant: str,
        *,
        search_query: str,
        filename: str | None = None,
        insight_create: bool = False,
        insight_use: bool = False,
        sources: list[dict[str, Any]] | None = None,
        used: bool = False,
    ) -> None:
        """本轮问答写入内存；不立即刷 Redis。"""
        human = HumanMessage(
            content=user,
            additional_kwargs={
                "search_query": search_query,
                "filename": filename or "",
                "insight_create": bool(insight_create),
                "insight_use": bool(insight_use),
                "used": bool(used),
            },
        )
        ai = AIMessage(
            content=assistant,
            additional_kwargs={
                "sources": list(sources or []),
                "used": bool(used),
            },
        )
        self.history.append(human)
        self.history.append(ai)
        self.pending_turns.append(PendingTurn(user=human, assistant=ai))
        self.touch()

    def flush_to_redis(self) -> None:
        """把尚未持久化的轮次写入 Redis（key = uuid::section_id）。"""
        if not self.pending_turns:
            return
        for turn in self.pending_turns:
            kwargs = dict(turn.user.additional_kwargs or {})
            if "insight_create" not in kwargs:
                kwargs["insight_create"] = False
                logger.warning(
                    "flush missing insight_create key=%s; default False",
                    self.key,
                )
            if "insight_use" not in kwargs:
                kwargs["insight_use"] = False
                logger.warning(
                    "flush missing insight_use key=%s; default False",
                    self.key,
                )
            if "used" not in kwargs:
                kwargs["used"] = False
            turn.user.additional_kwargs = kwargs
            ai_kwargs = dict(turn.assistant.additional_kwargs or {})
            if "used" not in ai_kwargs:
                ai_kwargs["used"] = False
            turn.assistant.additional_kwargs = ai_kwargs

        hist = get_history(self.uuid, self.section_id)
        for turn in self.pending_turns:
            hist.add_message(turn.user)
            hist.add_message(turn.assistant)
        logger.info(
            "flush history key=%s turns=%d",
            self.key,
            len(self.pending_turns),
        )
        self.pending_turns.clear()

    def finalize(self) -> None:
        """会话释放：清磁盘 → 未用切块 → 统一 filenames → 洞察入库 → 刷历史。"""
        from backend.llm.insight.registry import get_insight_registry

        section = self.section_insight
        if section is None:
            section = get_insight_registry().peek_section_insight(
                self.uuid, self.section_id
            )
        if section is not None:
            self.section_insight = section
            try:
                section.delete_disk_files()
            except Exception:
                logger.exception(
                    "delete_disk_files failed key=%s",
                    self.key,
                )
            try:
                section.delete_unused_files()
            except Exception:
                logger.exception(
                    "delete_unused_files failed key=%s",
                    self.key,
                )
            try:
                section.sync_filenames_with_used()
            except Exception:
                logger.exception(
                    "sync_filenames_with_used failed key=%s",
                    self.key,
                )
            try:
                section.save_to_redis()
            except Exception:
                logger.exception(
                    "section.save_to_redis failed key=%s",
                    self.key,
                )
            try:
                section._parent.save_to_redis()
            except Exception:
                logger.exception(
                    "user.save_to_redis failed key=%s",
                    self.key,
                )
        self.flush_to_redis()


def make_session_key(uuid: str, section_id: str) -> str:
    return make_history_session_id(uuid, section_id)


class AskSessionPool:
    """最多 MAX_SESSIONS 个会话；空闲超时 / 显式释放 / LRU 时 finalize。"""

    def __init__(
        self,
        max_size: int = MAX_SESSIONS,
        *,
        idle_seconds: float = SESSION_IDLE_SECONDS,
        sweep_interval: float = _IDLE_SWEEP_INTERVAL,
        start_sweeper: bool = True,
    ) -> None:
        self.max_size = max_size
        self.idle_seconds = idle_seconds
        self.sweep_interval = sweep_interval
        self._lock = threading.RLock()
        self._sessions: OrderedDict[str, AskSession] = OrderedDict()
        self._shared_graph: Any | None = None
        self._checkpointer: Any | None = None
        self._stop_sweeper = threading.Event()
        self._sweeper: threading.Thread | None = None
        if start_sweeper:
            self._start_sweeper()

    def _start_sweeper(self) -> None:
        if self._sweeper is not None and self._sweeper.is_alive():
            return

        def _loop() -> None:
            while not self._stop_sweeper.wait(self.sweep_interval):
                try:
                    self.sweep_idle()
                except Exception:
                    logger.exception("idle sweep failed")

        self._sweeper = threading.Thread(
            target=_loop,
            name="ask-session-idle-sweeper",
            daemon=True,
        )
        self._sweeper.start()

    def set_shared_graph(self, graph: Any, checkpointer: Any | None = None) -> None:
        with self._lock:
            self._shared_graph = graph
            self._checkpointer = checkpointer

    def get_shared_graph(self) -> Any | None:
        with self._lock:
            return self._shared_graph

    def get_or_create(
        self,
        uuid: str,
        section_id: str,
        *,
        load_history: bool = True,
    ) -> AskSession:
        uuid = _require_id("uuid", uuid)
        section_id = _require_id("section_id", section_id)
        self.sweep_idle()
        key = make_session_key(uuid, section_id)
        with self._lock:
            if key in self._sessions:
                session = self._sessions.pop(key)
                session.touch()
                self._sessions[key] = session
                if session.graph is None:
                    session.graph = self._shared_graph
                return session

            while len(self._sessions) >= self.max_size:
                self._evict_oldest_unlocked()

            history: list[BaseMessage] = []
            if load_history:
                history = list(get_history(uuid, section_id).messages)

            session = AskSession(
                uuid=uuid,
                section_id=section_id,
                history=history,
                graph=self._shared_graph,
            )
            self._sessions[key] = session
            logger.info(
                "session create key=%s pool_size=%d history_msgs=%d",
                key,
                len(self._sessions),
                len(history),
            )
            return session

    def peek_history_messages(self, uuid: str, section_id: str) -> list[BaseMessage]:
        """取完整历史：池内用内存副本，否则从 Redis 加载（不占/不驱逐池槽）。"""
        uuid = _require_id("uuid", uuid)
        section_id = _require_id("section_id", section_id)
        key = make_session_key(uuid, section_id)
        with self._lock:
            session = self._sessions.get(key)
            if session is not None:
                return list(session.history)
        return list(get_history(uuid, section_id).messages)

    def discard_session(self, uuid: str, section_id: str) -> bool:
        """从池中丢弃会话（不刷 Redis；用于删历史）。"""
        key = make_session_key(uuid, section_id)
        with self._lock:
            removed = self._sessions.pop(key, None) is not None
        if removed:
            try:
                drop_section_insight(uuid, section_id)
            except Exception:
                logger.exception("drop_section_insight failed key=%s", key)
            logger.info("session discard key=%s", key)
        return removed

    def discard_sessions_for_uuid(self, uuid: str) -> list[str]:
        """丢弃该 uuid 下所有内存会话（不刷 Redis；用于删历史）。"""
        uuid = _require_id("uuid", uuid)
        prefix = f"{uuid}::"
        with self._lock:
            keys = [k for k in self._sessions if k.startswith(prefix)]
            for key in keys:
                self._sessions.pop(key, None)
        for key in keys:
            parts = key.split("::", 1)
            if len(parts) == 2:
                try:
                    drop_section_insight(parts[0], parts[1])
                except Exception:
                    logger.exception("drop_section_insight failed key=%s", key)
        if keys:
            logger.info("session discard uuid=%s count=%d", uuid, len(keys))
        return keys

    def release_sessions_for_uuid(self, uuid: str) -> list[str]:
        """释放该 uuid 下所有内存会话并 finalize（刷 Redis + 删未用文件）。"""
        uuid = _require_id("uuid", uuid)
        prefix = f"{uuid}::"
        with self._lock:
            keys = [k for k in self._sessions if k.startswith(prefix)]
            sessions = [self._sessions.pop(k) for k in keys]
        for session in sessions:
            self._finalize_session(session)
        if keys:
            logger.info("session release uuid=%s count=%d", uuid, len(keys))
        return keys

    def release(self, uuid: str, section_id: str) -> None:
        """显式释放：删未用文件并刷 Redis。"""
        key = make_session_key(uuid, section_id)
        with self._lock:
            session = self._sessions.pop(key, None)
        if session is not None:
            self._finalize_session(session)
            logger.info("session release key=%s", key)

    def sweep_idle(self, *, now: float | None = None) -> list[str]:
        """释放空闲超过 idle_seconds 的会话。"""
        deadline = (now if now is not None else time.monotonic()) - self.idle_seconds
        with self._lock:
            stale_keys = [
                key
                for key, session in self._sessions.items()
                if session.last_used <= deadline
            ]
            sessions = [self._sessions.pop(k) for k in stale_keys]
        for session in sessions:
            self._finalize_session(session)
            logger.info("session idle-release key=%s", session.key)
        return stale_keys

    def flush_all(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            try:
                self._finalize_session(session)
            except Exception:
                logger.exception("flush_all failed key=%s", session.key)

    def _finalize_session(self, session: AskSession) -> None:
        try:
            session.finalize()
        except Exception:
            logger.exception("finalize failed key=%s", session.key)
        try:
            drop_section_insight(session.uuid, session.section_id)
        except Exception:
            logger.exception(
                "drop_section_insight failed key=%s",
                session.key,
            )

    def _evict_oldest_unlocked(self) -> None:
        if not self._sessions:
            return
        key, session = self._sessions.popitem(last=False)
        try:
            self._finalize_session(session)
        except Exception:
            logger.exception("evict finalize failed key=%s", key)
        logger.info("session evict key=%s remaining=%d", key, len(self._sessions))

    def reset(self) -> None:
        """测试用：不刷 Redis，直接清空。"""
        with self._lock:
            self._sessions.clear()
            self._shared_graph = None
            self._checkpointer = None


_pool = AskSessionPool()
atexit.register(_pool.flush_all)


def get_session_pool() -> AskSessionPool:
    return _pool
