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

from backend.llm.session.history import get_history, make_history_session_id

logger = logging.getLogger("backend.llm.graph.session_pool")

MAX_SESSIONS = 5


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
    """单个会话槽：内存 history，轮次结束刷 Redis。"""

    uuid: str
    section_id: str
    history: list[BaseMessage] = field(default_factory=list)
    pending_turns: list[PendingTurn] = field(default_factory=list)
    last_sources: list[dict[str, Any]] = field(default_factory=list)
    last_search_query: str = ""
    last_used: float = field(default_factory=time.monotonic)
    graph: Any | None = None

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
        sources: list[dict[str, Any]] | None = None,
    ) -> None:
        """本轮问答写入内存，并立即刷入 Redis。"""
        human = HumanMessage(
            content=user,
            additional_kwargs={
                "search_query": search_query,
                "filename": filename or "",
            },
        )
        ai = AIMessage(
            content=assistant,
            additional_kwargs={"sources": list(sources or [])},
        )
        self.history.append(human)
        self.history.append(ai)
        self.pending_turns.append(PendingTurn(user=human, assistant=ai))
        self.touch()
        self.flush_to_redis()

    def flush_to_redis(self) -> None:
        """把尚未持久化的轮次写入 Redis（key = uuid::section_id）。"""
        if not self.pending_turns:
            return
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


def make_session_key(uuid: str, section_id: str) -> str:
    return make_history_session_id(uuid, section_id)


class AskSessionPool:
    """最多 MAX_SESSIONS 个会话；超出时释放最久未使用的并刷 Redis。"""

    def __init__(self, max_size: int = MAX_SESSIONS) -> None:
        self.max_size = max_size
        self._lock = threading.RLock()
        self._sessions: OrderedDict[str, AskSession] = OrderedDict()
        self._shared_graph: Any | None = None
        self._checkpointer: Any | None = None

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

    def release(self, uuid: str, section_id: str) -> None:
        """显式释放并刷 Redis。"""
        key = make_session_key(uuid, section_id)
        with self._lock:
            session = self._sessions.pop(key, None)
        if session is not None:
            session.flush_to_redis()
            logger.info("session release key=%s", key)

    def flush_all(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            try:
                session.flush_to_redis()
            except Exception:
                logger.exception("flush_all failed key=%s", session.key)

    def _evict_oldest_unlocked(self) -> None:
        if not self._sessions:
            return
        key, session = self._sessions.popitem(last=False)
        try:
            session.flush_to_redis()
        except Exception:
            logger.exception("evict flush failed key=%s", key)
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
