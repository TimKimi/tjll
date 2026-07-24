"""按 (uuid, section_id) 管理 Ask 会话：内存历史 + LRU 池（最多 5 个）。"""

from __future__ import annotations

import atexit
import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from backend.llm.graph.history_window import (
    CompleteTurn,
    filter_chat_messages,
    iter_complete_turns,
    select_history_window,
)
from backend.llm.insight.registry import drop_section_insight
from backend.llm.insight.section import SectionInsight
from backend.llm.session.history import get_history, make_history_session_id

logger = logging.getLogger("backend.llm.graph.session_pool")

MAX_SESSIONS = 5
SESSION_IDLE_SECONDS = 120.0
_IDLE_SWEEP_INTERVAL = 30.0

MAINTAIN_TRIGGER_TURNS = 7
MAINTAIN_BATCH_TURNS = 4
# 维护落 Redis 时至少留在内存的最新完整轮次数（与 select_history_window 默认一致）
MEMORY_KEEP_TURNS = 3

MaintainFlag = Literal["idle", "active", "done"]

# 极简释放门闩：key=uuid::section_id；有 Event 且未 set → 释放中，排队 wait
_release_waiters: dict[str, threading.Event] = {}
_gate_lock = threading.Lock()


def wait_section_ready(uuid: str, section_id: str) -> None:
    """同 key 释放中则阻塞排队，结束后继续；异 section 不阻塞。"""
    key = make_history_session_id(uuid, section_id)
    with _gate_lock:
        ev = _release_waiters.get(key)
    if ev is not None:
        ev.wait()


def begin_section_release(uuid: str, section_id: str) -> bool:
    """登记释放中；若已在释放返回 False（防重入）。"""
    key = make_history_session_id(uuid, section_id)
    with _gate_lock:
        if key in _release_waiters:
            return False
        _release_waiters[key] = threading.Event()
        return True


def end_section_release(uuid: str, section_id: str) -> None:
    """放行并移除门闩，唤醒所有排队请求。"""
    key = make_history_session_id(uuid, section_id)
    with _gate_lock:
        ev = _release_waiters.pop(key, None)
    if ev is not None:
        ev.set()


def _require_id(name: str, value: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


def _msg_used(msg: BaseMessage) -> bool:
    extra = getattr(msg, "additional_kwargs", None) or {}
    return bool(extra.get("used", False))


def _history_msg_fingerprint(msg: BaseMessage) -> tuple[Any, ...]:
    """用于 Redis/内存历史去重的弱指纹。"""
    extra = getattr(msg, "additional_kwargs", None) or {}
    return (
        type(msg).__name__,
        str(getattr(msg, "content", "") or ""),
        str(extra.get("search_query") or ""),
        str(extra.get("filename") or ""),
        bool(extra.get("insight_create")),
        bool(extra.get("insight_use")),
        bool(extra.get("used")),
    )


def _set_msg_used(msg: BaseMessage, used: bool = True) -> None:
    kwargs = dict(getattr(msg, "additional_kwargs", None) or {})
    kwargs["used"] = bool(used)
    msg.additional_kwargs = kwargs


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
    last_detail: str = ""
    pending_ask: Any | None = None
    pending_enrich: dict[str, Any] = field(default_factory=dict)
    last_used: float = field(default_factory=time.monotonic)
    graph: Any | None = None
    section_insight: SectionInsight | None = None
    maintain_flag: MaintainFlag = "idle"
    _maintain_replica: SectionInsight | None = field(default=None, repr=False)
    _maintain_batch: list[CompleteTurn] = field(default_factory=list, repr=False)
    _maintain_lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    _maintain_finished: threading.Event = field(
        default_factory=threading.Event, repr=False
    )

    def __post_init__(self) -> None:
        # idle 时可立即通过等待
        self._maintain_finished.set()

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
        detail: str = "",
    ) -> None:
        """本轮问答写入内存；不立即刷 Redis。"""
        human = HumanMessage(
            content=user,
            additional_kwargs={
                "search_query": search_query,
                "detail": detail or "",
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

    def _ensure_turn_kwargs(self, turn: PendingTurn) -> None:
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

    def flush_to_redis(self) -> None:
        """释放/收尾：把内存中剩余完整轮次全部追加到 Redis。"""
        turns = iter_complete_turns(filter_chat_messages(self.history))
        if not turns:
            self.pending_turns.clear()
            return
        hist = get_history(self.uuid, self.section_id)
        for human, ai in turns:
            self._ensure_pair_kwargs(human, ai)
            hist.add_message(human)
            hist.add_message(ai)
        logger.info(
            "flush history key=%s turns=%d",
            self.key,
            len(turns),
        )
        self.pending_turns.clear()

    def _latest_keep_message_ids(self) -> set[int]:
        """当前内存中最新 MEMORY_KEEP_TURNS 完整轮次的消息 id。"""
        turns = iter_complete_turns(filter_chat_messages(self.history))
        if not turns:
            return set()
        keep = turns[-MEMORY_KEEP_TURNS:]
        return {id(m) for turn in keep for m in turn}

    def _flush_batch_to_redis(self, batch: list[CompleteTurn]) -> list[CompleteTurn]:
        """维护完成后：把内存里「非最新 KEEP 轮」且已 used 的轮次按时间序追加 Redis。

        不能只 flush ``batch`` 本身：加载进内存的更早 used 轮若晚于 batch 落库，
        会造成 Redis 时间序错乱。最新 ``MEMORY_KEEP_TURNS`` 轮仍留内存，待释放再写。

        ``batch`` 保留兼容调用方；落库集合按「keep 窗外 used」计算。
        返回实际已写入并应从内存 pop 的轮次。
        """
        _ = batch
        turns = iter_complete_turns(filter_chat_messages(self.history))
        if len(turns) <= MEMORY_KEEP_TURNS:
            return []
        keep_ids = self._latest_keep_message_ids()
        to_persist = [
            (h, a)
            for h, a in turns
            if id(h) not in keep_ids and (_msg_used(h) or _msg_used(a))
        ]
        if not to_persist:
            logger.info(
                "flush maintain skipped (no used outside keep-%d) key=%s",
                MEMORY_KEEP_TURNS,
                self.key,
            )
            return []

        pending_by_user = {id(t.user): t for t in self.pending_turns}
        hist = get_history(self.uuid, self.section_id)
        flushed: list[CompleteTurn] = []
        for human, ai in to_persist:
            pt = pending_by_user.get(id(human))
            if pt is not None:
                self._ensure_turn_kwargs(pt)
                hist.add_message(pt.user)
                hist.add_message(pt.assistant)
                flushed.append((pt.user, pt.assistant))
            else:
                # 启动从 Redis 装入的轮次不在 pending
                self._ensure_pair_kwargs(human, ai)
                hist.add_message(human)
                hist.add_message(ai)
                flushed.append((human, ai))

        flushed_ids = {id(h) for h, _ in flushed}
        self.pending_turns = [
            t for t in self.pending_turns if id(t.user) not in flushed_ids
        ]
        logger.info(
            "flush maintain key=%s flushed_turns=%d kept_in_memory=%d",
            self.key,
            len(flushed),
            min(MEMORY_KEEP_TURNS, len(turns)),
        )
        return flushed

    def _pop_batch_from_memory(self, batch: list[CompleteTurn]) -> None:
        ids = {id(m) for turn in batch for m in turn}
        self.history = [m for m in self.history if id(m) not in ids]
        self.pending_turns = [
            t
            for t in self.pending_turns
            if id(t.user) not in ids and id(t.assistant) not in ids
        ]

    def _ensure_pair_kwargs(self, human: BaseMessage, ai: BaseMessage) -> None:
        """释放 flush 时补齐消息侧车字段。"""
        h_kwargs = dict(getattr(human, "additional_kwargs", None) or {})
        if "insight_create" not in h_kwargs:
            h_kwargs["insight_create"] = False
        if "insight_use" not in h_kwargs:
            h_kwargs["insight_use"] = False
        if "used" not in h_kwargs:
            h_kwargs["used"] = False
        if "filename" not in h_kwargs:
            h_kwargs["filename"] = ""
        if "search_query" not in h_kwargs:
            h_kwargs["search_query"] = ""
        human.additional_kwargs = h_kwargs
        ai_kwargs = dict(getattr(ai, "additional_kwargs", None) or {})
        if "used" not in ai_kwargs:
            ai_kwargs["used"] = False
        if "sources" not in ai_kwargs:
            ai_kwargs["sources"] = []
        ai.additional_kwargs = ai_kwargs

    def _on_maintain_done(self) -> None:
        """异步维护结束：只置 done。"""
        with self._maintain_lock:
            self.maintain_flag = "done"
            self._maintain_finished.set()
            logger.info("maintain done flag key=%s", self.key)

    def _wait_until_maintain_idle(self) -> None:
        """等到 maintain 回到 idle。

        - ``done``：先把维护副本融合进本体（并释放 occupied）
        - ``active``：等到结束后再融合
        """
        while True:
            with self._maintain_lock:
                if self.maintain_flag == "idle":
                    return
                if self.maintain_flag == "done":
                    self._apply_maintain_done()
                    continue
                ev = self._maintain_finished
            ev.wait(timeout=1.0)

    def _apply_maintain_done(self) -> None:
        """阻塞：flush used 批 + pop + 副本融合本体 + save/split → 释放 occupied → idle。"""
        batch = list(self._maintain_batch)
        replica = self._maintain_replica
        self._maintain_batch = []
        self._maintain_replica = None
        parent = None

        try:
            try:
                flushed = self._flush_batch_to_redis(batch)
                self._pop_batch_from_memory(flushed)
            except Exception:
                logger.exception("maintain flush/pop failed key=%s", self.key)

            section = self.section_insight
            if section is None:
                from backend.llm.insight.registry import get_insight_registry

                section = get_insight_registry().peek_section_insight(
                    self.uuid, self.section_id
                )
                self.section_insight = section

            if section is not None:
                parent = section._parent

            if section is not None and replica is not None:
                try:
                    section_changed, user_changed = section.merge_from_maintain_replica(
                        replica
                    )
                    section.save_to_redis()
                    section._parent.save_to_redis()
                    if section_changed:
                        section.split_and_store_section()
                    if user_changed:
                        section.split_and_store()
                except Exception:
                    logger.exception(
                        "maintain merge/save/split failed key=%s", self.key
                    )
        finally:
            if parent is not None:
                parent.release_occupied()
            self.maintain_flag = "idle"
            self._maintain_finished.set()
            logger.info(
                "maintain applied key=%s history_msgs=%d",
                self.key,
                len(self.history),
            )

    def _resolve_live_parent(self):
        """取 live section 的共享 parent；无则 None。"""
        section = self.section_insight
        if section is None:
            from backend.llm.insight.registry import get_insight_registry

            section = get_insight_registry().peek_section_insight(
                self.uuid, self.section_id
            )
            self.section_insight = section
        if section is None:
            return None
        return section._parent

    def _maintain_remaining_for_release(self) -> None:
        """释放收尾：无轮数门槛；剩余 unused 全部 used=true 并同步维护一次。

        调用前应已 ``_wait_until_maintain_idle``（done 副本已融合、occupied 已释放）。
        此处再检查 occupied：为 True（他会话占用）则等待；否则抢占后继续。
        """
        with self._maintain_lock:
            turns = iter_complete_turns(filter_chat_messages(self.history))
            unused = [t for t in turns if not (_msg_used(t[0]) or _msg_used(t[1]))]
            if not unused:
                return

            for human, ai in unused:
                _set_msg_used(human, True)
                _set_msg_used(ai, True)

            live = self.section_insight
            if live is None:
                from backend.llm.insight.registry import get_insight_registry

                live = get_insight_registry().peek_section_insight(
                    self.uuid, self.section_id
                )
                self.section_insight = live

            if live is None:
                try:
                    flushed = self._flush_batch_to_redis(unused)
                    self._pop_batch_from_memory(flushed)
                except Exception:
                    logger.exception(
                        "release maintain flush without section failed key=%s",
                        self.key,
                    )
                return

        parent = live._parent
        # 融合后一般为 False；若仍 True 则等待空闲后再抢占（设为 True）
        if parent.occupied:
            logger.info(
                "release wait occupied before remaining maintain key=%s",
                self.key,
            )
        parent.wait_acquire_occupied()
        applied = False
        try:
            with self._maintain_lock:
                replica = live.clone_for_maintain()
                insight_create_turns = [
                    t
                    for t in unused
                    if bool((t[0].additional_kwargs or {}).get("insight_create"))
                ]
                self._maintain_replica = replica
                self._maintain_batch = list(unused)
                self._maintain_finished.clear()
                self.maintain_flag = "active"

            try:
                replica.total_maintain(
                    unused,
                    insight_create_turns=insight_create_turns,
                    on_done=self._on_maintain_done,
                )
            except Exception:
                logger.exception("release maintain failed key=%s", self.key)
                self._on_maintain_done()

            with self._maintain_lock:
                if self.maintain_flag == "done":
                    self._apply_maintain_done()
                    applied = True
        finally:
            if not applied:
                parent.release_occupied()

    def maintain(self) -> None:
        """三态维护：done 先合并；occupied 则跳过；idle 达阈值则开批。"""
        with self._maintain_lock:
            while True:
                if self.maintain_flag == "done":
                    self._apply_maintain_done()
                    continue

                parent = self._resolve_live_parent()
                if parent is not None and parent.occupied:
                    return

                if self.maintain_flag == "active":
                    return

                turns = iter_complete_turns(filter_chat_messages(self.history))
                unused = [t for t in turns if not (_msg_used(t[0]) or _msg_used(t[1]))]
                if (
                    len(turns) < MAINTAIN_TRIGGER_TURNS
                    or len(unused) < MAINTAIN_BATCH_TURNS
                ):
                    return

                live = self.section_insight
                if live is None:
                    from backend.llm.insight.registry import ensure_section_insight

                    live = ensure_section_insight(self.uuid, self.section_id)
                    self.section_insight = live

                if not live._parent.try_acquire_occupied():
                    return

                batch = unused[:MAINTAIN_BATCH_TURNS]
                for human, ai in batch:
                    _set_msg_used(human, True)
                    _set_msg_used(ai, True)

                replica = live.clone_for_maintain()
                insight_create_turns = [
                    t
                    for t in batch
                    if bool((t[0].additional_kwargs or {}).get("insight_create"))
                ]
                self._maintain_replica = replica
                self._maintain_batch = list(batch)
                self._maintain_finished.clear()
                self.maintain_flag = "active"

                def _run(
                    rep: SectionInsight = replica,
                    turns_batch: list[CompleteTurn] = batch,
                    create_turns: list[CompleteTurn] = insight_create_turns,
                    done: Callable[[], None] = self._on_maintain_done,
                ) -> None:
                    try:
                        rep.total_maintain(
                            turns_batch,
                            insight_create_turns=create_turns,
                            on_done=done,
                        )
                    except Exception:
                        logger.exception("maintain thread failed key=%s", self.key)
                        done()

                threading.Thread(
                    target=_run,
                    name=f"ask-maintain-{self.key}",
                    daemon=True,
                ).start()
                logger.info(
                    "maintain started key=%s batch=%d",
                    self.key,
                    len(batch),
                )
                return

    def finalize(self) -> None:
        """同步收尾（atexit 等）：等同 release worker 主体。"""
        self._wait_until_maintain_idle()
        self._maintain_remaining_for_release()
        self._cleanup_and_persist()

    def _cleanup_and_persist(self) -> None:
        """磁盘清理 + 洞察 save + 聊天 flush。section 仅 peek，不强行 ensure。"""
        from backend.llm.insight.registry import get_insight_registry

        section = self.section_insight
        if section is None:
            section = get_insight_registry().peek_section_insight(
                self.uuid, self.section_id
            )
        if section is not None:
            self.section_insight = section
            parent = section._parent
            parent.wait_acquire_occupied()
            try:
                try:
                    section.delete_disk_files()
                except Exception:
                    logger.exception("delete_disk_files failed key=%s", self.key)
                try:
                    section.delete_unused_files()
                except Exception:
                    logger.exception("delete_unused_files failed key=%s", self.key)
                try:
                    section.sync_filenames_with_used()
                except Exception:
                    logger.exception("sync_filenames_with_used failed key=%s", self.key)
                try:
                    section.save_to_redis()
                except Exception:
                    logger.exception("section.save_to_redis failed key=%s", self.key)
                try:
                    section._parent.save_to_redis()
                except Exception:
                    logger.exception("user.save_to_redis failed key=%s", self.key)
            finally:
                parent.release_occupied()
        self.flush_to_redis()


def _consume_loaded_history_from_redis(
    uuid: str,
    section_id: str,
    raw: list[BaseMessage],
    loaded: list[BaseMessage],
) -> None:
    """启动装入内存的消息从 Redis 删除，避免之后 flush 重复追加。

    ``loaded`` 必须来自同一次 ``raw`` 读出的对象引用（按 ``id`` 匹配）。
    """
    if not loaded:
        return
    loaded_ids = {id(m) for m in loaded}
    remaining = [m for m in raw if id(m) not in loaded_ids]
    hist = get_history(uuid, section_id)
    hist.clear()
    for msg in remaining:
        hist.add_message(msg)
    logger.info(
        "consume redis history uuid=%s section_id=%s loaded_msgs=%d remaining_msgs=%d",
        uuid,
        section_id,
        len(loaded),
        len(remaining),
    )


def make_session_key(uuid: str, section_id: str) -> str:
    return make_history_session_id(uuid, section_id)


def session_history(uuid: str, section_id: str) -> list[BaseMessage]:
    """从图节点/路由读取内存历史；不从 Redis 重载。"""
    session = get_session_pool().get_or_create(
        uuid,
        section_id,
        load_history=False,
    )
    return list(session.history)


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
                # 走本模块 get_history，便于测试 monkeypatch
                raw = list(get_history(uuid, section_id).messages)
                history = select_history_window(raw)
                # 已装入内存的从 Redis 摘除，释放时再整段写回，避免重复
                try:
                    _consume_loaded_history_from_redis(uuid, section_id, raw, history)
                except Exception:
                    logger.exception(
                        "consume redis history failed key=%s",
                        key,
                    )

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
        return filter_chat_messages(list(get_history(uuid, section_id).messages))

    def merged_history_messages(self, uuid: str, section_id: str) -> list[BaseMessage]:
        """Redis 已落盘历史 + AskSession 内存历史（去重后拼接）。"""
        uuid = _require_id("uuid", uuid)
        section_id = _require_id("section_id", section_id)
        redis_msgs = filter_chat_messages(list(get_history(uuid, section_id).messages))
        key = make_session_key(uuid, section_id)
        with self._lock:
            session = self._sessions.get(key)
            if session is None:
                return list(redis_msgs)
            mem = filter_chat_messages(list(session.history))
        seen = {_history_msg_fingerprint(m) for m in redis_msgs}
        out = list(redis_msgs)
        for m in mem:
            fp = _history_msg_fingerprint(m)
            if fp in seen:
                continue
            seen.add(fp)
            out.append(m)
        return out

    def first_memory_user_query(self, uuid: str, section_id: str) -> str:
        """仅查池内内存：首条完整轮用户 content；无会话/无轮次返回 ``\"\"``。"""
        uuid = _require_id("uuid", uuid)
        section_id = _require_id("section_id", section_id)
        key = make_session_key(uuid, section_id)
        with self._lock:
            session = self._sessions.get(key)
            if session is None:
                return ""
            history = list(session.history)
        turns = iter_complete_turns(filter_chat_messages(history))
        if not turns:
            return ""
        content = turns[0][0].content
        if content is None:
            return ""
        return str(content)

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
        """释放该 uuid 下所有内存会话（各 section 异步收尾，立即返回）。"""
        uuid = _require_id("uuid", uuid)
        prefix = f"{uuid}::"
        with self._lock:
            keys = [k for k in self._sessions if k.startswith(prefix)]
            sessions = [self._sessions.pop(k) for k in keys]
        for session in sessions:
            self._kick_release_worker(session)
        if keys:
            logger.info("session release uuid=%s count=%d", uuid, len(keys))
        return keys

    def release(self, uuid: str, section_id: str) -> bool:
        """显式释放：立刻返回；后台维护剩余轮次并落 Redis。"""
        uuid = _require_id("uuid", uuid)
        section_id = _require_id("section_id", section_id)
        if not begin_section_release(uuid, section_id):
            return True
        key = make_session_key(uuid, section_id)
        with self._lock:
            session = self._sessions.pop(key, None)
        if session is None:
            end_section_release(uuid, section_id)
            return True
        self._kick_release_worker(session, owns_gate=True)
        logger.info("session release scheduled key=%s", key)
        return True

    def sweep_idle(self, *, now: float | None = None) -> list[str]:
        """释放空闲超过 idle_seconds 的会话（异步收尾）。"""
        deadline = (now if now is not None else time.monotonic()) - self.idle_seconds
        with self._lock:
            stale_keys = [
                key
                for key, session in self._sessions.items()
                if session.last_used <= deadline
            ]
            sessions = [self._sessions.pop(k) for k in stale_keys]
        for session in sessions:
            self._kick_release_worker(session)
            logger.info("session idle-release scheduled key=%s", session.key)
        return stale_keys

    def flush_all(self) -> None:
        """进程退出：同步收尾，避免丢数据。"""
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            owned = begin_section_release(session.uuid, session.section_id)
            try:
                self._release_worker(session)
            except Exception:
                logger.exception("flush_all failed key=%s", session.key)
            finally:
                if owned:
                    end_section_release(session.uuid, session.section_id)

    def _kick_release_worker(
        self, session: AskSession, *, owns_gate: bool | None = None
    ) -> None:
        """后台跑 release worker；owns_gate=None 时尝试 begin。"""
        if owns_gate is None:
            owns_gate = begin_section_release(session.uuid, session.section_id)

        def worker() -> None:
            try:
                self._release_worker(session)
            finally:
                if owns_gate:
                    end_section_release(session.uuid, session.section_id)

        threading.Thread(
            target=worker,
            name=f"ask-release-{session.key}",
            daemon=True,
        ).start()

    def _release_worker(self, session: AskSession) -> None:
        """释放后台：done 先融合副本 → 再处理 occupied → 维护全部 unused → 落盘。"""
        try:
            # 1) active 等到结束；done 则把副本融合进本体并释放 occupied
            session._wait_until_maintain_idle()
            # 2) occupied 仍为 True 则等待；否则抢占后维护全部未 used 轮次
            session._maintain_remaining_for_release()
            session._cleanup_and_persist()
        except Exception:
            logger.exception("release worker failed key=%s", session.key)
        try:
            drop_section_insight(session.uuid, session.section_id)
        except Exception:
            logger.exception(
                "drop_section_insight failed key=%s",
                session.key,
            )

    def _finalize_session(self, session: AskSession) -> None:
        """兼容旧同步路径：直接跑 worker（调用方自管门闩）。"""
        self._release_worker(session)

    def _evict_oldest_unlocked(self) -> None:
        if not self._sessions:
            return
        key, session = self._sessions.popitem(last=False)
        self._kick_release_worker(session)
        logger.info("session evict key=%s remaining=%d", key, len(self._sessions))

    def reset(self) -> None:
        """测试用：不刷 Redis，直接清空。"""
        with self._lock:
            self._sessions.clear()
            self._shared_graph = None
            self._checkpointer = None
        with _gate_lock:
            _release_waiters.clear()


_pool = AskSessionPool()
atexit.register(_pool.flush_all)


def get_session_pool() -> AskSessionPool:
    return _pool
