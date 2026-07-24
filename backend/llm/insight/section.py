"""会话洞察：继承 UserInsight，增加会话属性 / facts / review / 文档切块。"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import StructuredTool

from backend.config import settings
from backend.llm.insight.model import (
    UserInsight,
    format_attr_line,
    format_attrs_concat,
    insight_os_threshold,
)
from backend.rag.document.chunking import split_text_to_chunks
from backend.rag.document.clean import clean_text
from backend.rag.document.indexing import (
    delete_section_document_from_opensearch,
    delete_section_insight_from_opensearch,
    index_section_document_chunks,
    index_section_insight_chunks,
)
from backend.rag.document.loaders import load_document_as_text
from backend.rag.document.paths import (
    SUPPORTED_EXTS,
    normalize_backend_path,
    resolve_repo_path,
)
from backend.rag.retrieve.search import (
    search_section_document_texts,
    search_section_insight_text,
)

logger = logging.getLogger("backend.llm.insight.section")

_SEGMENT_SEP = "\n\n\n"
_ATTR_SEP = "\n"


def _normalize_path_list(paths: str | list[str]) -> list[str]:
    """将单个路径或路径列表规范为 ``./backend/...``。"""
    if isinstance(paths, str):
        raw = [paths]
    elif isinstance(paths, list):
        raw = paths
    else:
        raise TypeError("paths must be str or list[str]")
    out: list[str] = []
    for item in raw:
        text = str(item or "").strip()
        if not text:
            continue
        norm = normalize_backend_path(text)
        if norm:
            out.append(norm)
    return out


class SectionInsight(UserInsight):
    """按 uuid + section_id 绑定的会话洞察。

    - 用户级 ``_attrs`` / ``search`` / ``split_and_store``：委托共享的 ``UserInsight`` 父实例
    - ``_section_attrs``：本会话独有属性（独立索引）
    - ``_filenames`` / ``_used_filenames`` / 文档索引：上传文件切块
    - ``_facts`` / ``_review``：仅内存
    """

    def __init__(
        self,
        uuid: str,
        section_id: str,
        *,
        parent: UserInsight | None = None,
    ) -> None:
        sid = (section_id or "").strip()
        if not sid:
            raise ValueError("section_id is required")
        # 不调用 UserInsight.__init__：用户级状态落在共享 parent 上
        self._parent: UserInsight = parent if parent is not None else UserInsight(uuid)
        self.uuid = self._parent.uuid
        self.section_id = sid
        self._filenames: list[str] = []
        self._used_filenames: list[str] = []
        self._section_attrs: dict[str, str] = {}
        self._facts: list[str] = []
        self._review: str = ""
        self.last_section_chunk_size: int = 0
        self.max_section_attr_len: int = 0
        self.attrs_len: int = 0

    # ── 用户级洞察（共享 parent）──────────────────────────────

    @property
    def _attrs(self) -> dict[str, str]:
        return self._parent._attrs

    @_attrs.setter
    def _attrs(self, value: dict[str, str]) -> None:
        self._parent._attrs = value

    @property
    def last_chunk_size(self) -> int:
        return self._parent.last_chunk_size

    @last_chunk_size.setter
    def last_chunk_size(self, value: int) -> None:
        self._parent.last_chunk_size = value

    @property
    def max_attr_len(self) -> int:
        return self._parent.max_attr_len

    @max_attr_len.setter
    def max_attr_len(self, value: int) -> None:
        self._parent.max_attr_len = value

    def as_dict(self) -> dict[str, str]:
        return self._parent.as_dict()

    def batch_add(self, attrs: dict[str, Any]) -> dict[str, str]:
        return self._parent.batch_add(attrs)

    def as_batch_add_tool(self) -> StructuredTool:
        return self._parent.as_batch_add_tool()

    def to_long_text(self, size: int | None = None) -> str:
        return self._parent.to_long_text(size)

    def split_and_store(self) -> int:
        return self._parent.split_and_store()

    def search(self, query: str) -> str:
        return self._parent.search(query)

    # ── 文档名列表 ────────────────────────────────────────────

    def filenames(self) -> list[str]:
        return list(self._filenames)

    def used_filenames(self) -> list[str]:
        return list(self._used_filenames)

    def add_used_filenames(self, paths: str | list[str]) -> list[str]:
        """标记已使用的文件（仓库相对路径）；供外部脚本调用。"""
        for source_file in _normalize_path_list(paths):
            if source_file not in self._used_filenames:
                self._used_filenames.append(source_file)
        logger.info(
            "add_used_filenames uuid=%s section_id=%s used=%d",
            self.uuid,
            self.section_id,
            len(self._used_filenames),
        )
        return self.used_filenames()

    def delete_unused_files(self) -> list[str]:
        """删除 ``_filenames`` 有而 ``_used_filenames`` 无的文档切块。"""
        used = set(self._used_filenames)
        unused = [f for f in self._filenames if f not in used]
        deleted: list[str] = []
        for source_file in unused:
            try:
                delete_section_document_from_opensearch(
                    self.uuid,
                    self.section_id,
                    source_file=source_file,
                )
            except Exception:
                logger.exception(
                    "delete_unused_files failed uuid=%s section_id=%s file=%s",
                    self.uuid,
                    self.section_id,
                    source_file,
                )
                continue
            deleted.append(source_file)
        if deleted:
            deleted_set = set(deleted)
            self._filenames = [f for f in self._filenames if f not in deleted_set]
        logger.info(
            "delete_unused_files uuid=%s section_id=%s deleted=%d",
            self.uuid,
            self.section_id,
            len(deleted),
        )
        return deleted

    def delete_disk_files(self) -> list[str]:
        """按 ``_filenames`` 检测磁盘：存在则删除本体（会话释放时调用）。"""
        removed: list[str] = []
        for source_file in list(self._filenames):
            try:
                path = resolve_repo_path(source_file)
            except Exception:
                logger.exception(
                    "delete_disk_files resolve failed uuid=%s section_id=%s file=%s",
                    self.uuid,
                    self.section_id,
                    source_file,
                )
                continue
            try:
                if path.is_file():
                    path.unlink()
                    removed.append(source_file)
                    logger.info(
                        "delete_disk_files removed uuid=%s section_id=%s path=%s",
                        self.uuid,
                        self.section_id,
                        path,
                    )
            except Exception:
                logger.exception(
                    "delete_disk_files unlink failed uuid=%s section_id=%s path=%s",
                    self.uuid,
                    self.section_id,
                    path,
                )
        return removed

    def sync_filenames_with_used(self) -> None:
        """会话结束统一字段：``_filenames`` 与 ``_used_filenames`` 一致。"""
        self._filenames = list(self._used_filenames)

    def save_to_redis(self) -> None:
        """持久化会话洞察到 Redis（不含父类 attrs）。"""
        from backend.llm.insight.store import save_section_insight

        save_section_insight(self)

    @classmethod
    def load_from_redis(cls, uuid: str) -> UserInsight | None:
        """不支持：请用 ``load_section_from_redis``。"""
        raise TypeError(
            "SectionInsight.load_from_redis is unsupported; "
            "use load_section_from_redis(uuid, section_id, parent=...)"
        )

    @classmethod
    def load_section_from_redis(
        cls,
        uuid: str,
        section_id: str,
        *,
        parent: UserInsight,
    ) -> SectionInsight | None:
        """从 Redis 加载并挂到 parent；不存在返回 None。"""
        from backend.llm.insight.store import load_section_insight

        return load_section_insight(uuid, section_id, parent=parent)

    # ── 会话属性（对齐父类 _attrs）────────────────────────────

    def section_as_dict(self) -> dict[str, str]:
        return dict(self._section_attrs)

    def _section_attrs_concat(self) -> str:
        return format_attrs_concat(self._section_attrs)

    def _recompute_attrs_len(self) -> None:
        self.attrs_len = len(self._section_attrs_concat())

    def _recompute_max_section_attr_len(self) -> None:
        if not self._section_attrs:
            self.max_section_attr_len = 0
            return
        self.max_section_attr_len = max(
            len(format_attr_line(k, v)) for k, v in self._section_attrs.items()
        )

    def batch_add_section(self, attrs: dict[str, Any]) -> dict[str, str]:
        """批量添加/覆盖会话独有数据属性。"""
        if not isinstance(attrs, dict):
            raise TypeError("attrs must be a dict")
        for key, value in attrs.items():
            k = str(key).strip()
            if not k or value is None:
                continue
            self._section_attrs[k] = str(value)
        self._recompute_max_section_attr_len()
        self._recompute_attrs_len()
        logger.info(
            "batch_add_section uuid=%s section_id=%s attrs=%d attrs_len=%d",
            self.uuid,
            self.section_id,
            len(self._section_attrs),
            self.attrs_len,
        )
        return self.section_as_dict()

    def replace_section_attrs(self, attrs: dict[str, Any] | None) -> dict[str, str]:
        """用新字典整体覆盖会话属性（先清空再写入）。"""
        if attrs is None:
            attrs = {}
        if not isinstance(attrs, dict):
            raise TypeError("attrs must be a dict")
        self._section_attrs.clear()
        return self.batch_add_section(attrs)

    def as_batch_add_section_tool(self) -> StructuredTool:
        def _tool(attrs: dict[str, Any]) -> dict[str, str]:
            """批量写入本会话洞察数据属性。

            Args:
                attrs: 键值对字典，例如 ``{"本次预算": "200", "同行人数": "3"}``。
            """
            return self.batch_add_section(attrs)

        return StructuredTool.from_function(
            func=_tool,
            name="batch_add_section_insight_attrs",
            description=(
                "批量添加或更新【本会话】洞察数据属性。"
                "参数 attrs 为字典，键为属性名，值为属性内容。"
            ),
        )

    def to_section_long_text(self, size: int | None = None) -> str:
        """将会话属性按段长规则拼成长文（段间 ``\\n\\n\\n``）。"""
        if not self._section_attrs:
            return ""

        requested = settings.insight_chunk_size if size is None else int(size)
        if requested < 1:
            requested = 1
        limit = (
            self.max_section_attr_len
            if self.max_section_attr_len > 0 and requested < self.max_section_attr_len
            else requested
        )
        if limit < 1:
            limit = 1

        parts = [format_attr_line(k, v) for k, v in self._section_attrs.items()]
        out = ""
        segment_len = 0
        for piece in parts:
            if segment_len == 0:
                if out:
                    out += _SEGMENT_SEP
                out += piece
                segment_len = len(piece)
                continue
            addition = _ATTR_SEP + piece
            if segment_len + len(addition) <= limit:
                out += addition
                segment_len += len(addition)
            else:
                out += _SEGMENT_SEP + piece
                segment_len = len(piece)
        return out

    def split_and_store_section(self) -> int:
        """会话属性拼文 → 按 ``\\n\\n\\n`` 切割 → 写入 section_insight 索引。"""
        if self.attrs_len < insight_os_threshold():
            return 0

        text = self.to_section_long_text(settings.insight_chunk_size)
        if not text.strip():
            if self.last_section_chunk_size > 0:
                delete_section_insight_from_opensearch(self.uuid, self.section_id)
                self.last_section_chunk_size = 0
            return 0

        chunks = split_text_to_chunks(
            text,
            chunk_size=max(len(text), 1),
            chunk_overlap=0,
            separators=[_SEGMENT_SEP],
        )
        chunks = [c for c in chunks if c.strip()]
        n = len(chunks)

        if 0 < n < self.last_section_chunk_size:
            delete_section_insight_from_opensearch(self.uuid, self.section_id)

        index_section_insight_chunks(self.uuid, self.section_id, chunks, ensure=True)
        self.last_section_chunk_size = n
        logger.info(
            "split_and_store_section uuid=%s section_id=%s chunks=%d",
            self.uuid,
            self.section_id,
            n,
        )
        return n

    def search_section(self, query: str) -> str:
        """低于门槛返回全量拼接；否则检索本会话属性切块。"""
        if self.attrs_len < insight_os_threshold():
            return self._section_attrs_concat()
        if self.last_section_chunk_size <= 0:
            return ""
        return search_section_insight_text(
            query, uuid=self.uuid, section_id=self.section_id
        )

    # ── facts ────────────────────────────────────────────────

    def get_facts(self) -> list[str]:
        return list(self._facts)

    def set_facts(self, items: list[str] | None = None) -> list[str]:
        """整体覆写 facts 列表（每条 ≤20 字）。"""
        if items is None:
            items = []
        if not isinstance(items, list):
            raise TypeError("items must be a list of strings")
        self._facts = [str(x).strip()[:20] for x in items if str(x).strip()]
        logger.info(
            "set_facts uuid=%s section_id=%s total=%d",
            self.uuid,
            self.section_id,
            len(self._facts),
        )
        return self.get_facts()

    def add_facts(
        self,
        start: int | None = None,
        items: list[str] | None = None,
    ) -> list[str]:
        """增加 facts。

        - ``start is None``：追加 ``items``
        - ``start`` 为 1-based：保留前 ``start-1`` 条，删除从第 start 条到末尾，再追加
        """
        if items is None:
            items = []
        if not isinstance(items, list):
            raise TypeError("items must be a list of strings")
        cleaned = [str(x).strip()[:20] for x in items if str(x).strip()]

        if start is None:
            self._facts.extend(cleaned)
        else:
            idx = int(start)
            if idx < 1:
                raise ValueError("start must be >= 1 when provided")
            # 1-based：保留 [:start-1]
            keep = max(0, idx - 1)
            self._facts = self._facts[:keep]
            self._facts.extend(cleaned)

        logger.info(
            "add_facts uuid=%s section_id=%s start=%s total=%d",
            self.uuid,
            self.section_id,
            start,
            len(self._facts),
        )
        return self.get_facts()

    def as_add_facts_tool(self) -> StructuredTool:
        def _tool(
            items: list[str],
            start: int | None = None,
        ) -> list[str]:
            """追加或从指定条目起截断后写入 facts。

            Args:
                items: 要追加的字符串列表。
                start: 1-based 起始条号；为空则直接追加。传入 N 表示删除原第 N 条及之后再追加。
            """
            return self.add_facts(start=start, items=items)

        return StructuredTool.from_function(
            func=_tool,
            name="add_section_facts",
            description=(
                "向本会话 facts 列表追加内容。"
                "items 为字符串列表；start 可选（从 1 起），"
                "表示从第 start 条起删除旧内容后再追加。"
            ),
        )

    # ── review ───────────────────────────────────────────────

    def get_review(self) -> str:
        return self._review

    def get_review_with_fallback(self) -> str:
        """review 非空原样返回；否则回落池内内存首条用户 query，找不到则 ``\"\"``。"""
        text = (self._review or "").strip()
        if text:
            return self._review
        from backend.llm.graph.session_pool import get_session_pool

        return get_session_pool().first_memory_user_query(self.uuid, self.section_id)

    def set_review(self, text: str) -> str:
        body = "" if text is None else str(text).strip()
        if len(body) > 150:
            body = body[:150]
        self._review = body
        logger.info(
            "set_review uuid=%s section_id=%s len=%d",
            self.uuid,
            self.section_id,
            len(self._review),
        )
        return self._review

    def as_set_review_tool(self) -> StructuredTool:
        def _tool(text: str) -> str:
            """覆盖写入本会话 review 文本。

            Args:
                text: 完整 review 正文。
            """
            return self.set_review(text)

        return StructuredTool.from_function(
            func=_tool,
            name="set_section_review",
            description="设置或覆盖本会话的 review 字符串。",
        )

    def as_get_review_tool(self) -> StructuredTool:
        def _tool() -> str:
            """读取本会话 review 摘要（空则回落首条用户 query）。"""
            return self.get_review_with_fallback()

        return StructuredTool.from_function(
            func=_tool,
            name="get_section_review",
            description="读取本会话 review 摘要字符串。",
        )

    def as_get_facts_tool(self) -> StructuredTool:
        def _tool() -> list[str]:
            """读取本会话 facts 列表。"""
            return self.get_facts()

        return StructuredTool.from_function(
            func=_tool,
            name="get_section_facts",
            description="读取本会话 facts 字符串列表。",
        )

    # ── 维护（副本上执行）──────────────────────────────────────

    def clone_for_maintain(self) -> SectionInsight:
        """深拷贝会话字段；用户 attrs 使用独立快照 parent（不持有 occupied）。"""
        snap = UserInsight(self.uuid)
        snap._attrs = dict(self._parent._attrs)
        snap.last_chunk_size = int(self._parent.last_chunk_size)
        snap.max_attr_len = int(self._parent.max_attr_len)
        snap.attrs_len = int(self._parent.attrs_len)
        clone = SectionInsight(self.uuid, self.section_id, parent=snap)
        clone._filenames = list(self._filenames)
        clone._used_filenames = list(self._used_filenames)
        clone._section_attrs = dict(self._section_attrs)
        clone._facts = list(self._facts)
        clone._review = self._review
        clone.last_section_chunk_size = int(self.last_section_chunk_size)
        clone.max_section_attr_len = int(self.max_section_attr_len)
        clone.attrs_len = int(self.attrs_len)
        return clone

    def merge_from_maintain_replica(self, replica: SectionInsight) -> tuple[bool, bool]:
        """合并维护副本；返回 (section_attrs 有变, user_attrs 有变)。"""
        section_changed = dict(replica._section_attrs) != dict(self._section_attrs)
        user_changed = dict(replica._parent._attrs) != dict(self._parent._attrs)
        self._facts = list(replica._facts)
        self._review = str(replica._review or "")
        self._section_attrs = dict(replica._section_attrs)
        self._recompute_max_section_attr_len()
        self._recompute_attrs_len()
        if user_changed:
            self._parent._attrs = dict(replica._parent._attrs)
            self._parent._recompute_max_attr_len()
            self._parent._recompute_attrs_len()
        return section_changed, user_changed

    @staticmethod
    def _history_text(messages: list[Any]) -> str:
        from langchain_core.messages import AIMessage, HumanMessage

        lines: list[str] = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            else:
                role = "other"
            lines.append(f"{role}: {getattr(msg, 'content', '')}")
        return "\n".join(lines)

    def maintain_review(self, history: list[Any]) -> None:
        """LLM + set_review；review ≤150 字。"""
        from backend.llm.client.tool_loop import run_tool_loop
        from backend.llm.prompts.maintain import MAINTAIN_REVIEW_PROMPT

        messages = MAINTAIN_REVIEW_PROMPT.format_messages(
            review=self.get_review() or "（空）",
            history_text=self._history_text(history) or "（空）",
        )
        run_tool_loop(
            messages,
            [self.as_set_review_tool()],
            temperature=settings.llm_generate_temperature,
            max_rounds=4,
        )

    def maintain_facts(self, history: list[Any]) -> None:
        """LLM + add_facts；单条 ≤20 字。"""
        from backend.llm.client.tool_loop import run_tool_loop
        from backend.llm.prompts.maintain import MAINTAIN_FACTS_PROMPT

        facts = self.get_facts()
        facts_text = "\n".join(f"{i + 1}. {x}" for i, x in enumerate(facts)) or "（空）"
        messages = MAINTAIN_FACTS_PROMPT.format_messages(
            facts_text=facts_text,
            history_text=self._history_text(history) or "（空）",
        )
        run_tool_loop(
            messages,
            [self.as_add_facts_tool()],
            temperature=settings.llm_generate_temperature,
            max_rounds=6,
        )

    def maintain_section_attrs(
        self,
        history: list[Any],
        *,
        insight_create_turns: list[Any] | None = None,
    ) -> None:
        """维护会话属性；若有 insight_create 轮次则再维护用户属性。"""
        from backend.llm.client.tool_loop import run_tool_loop
        from backend.llm.prompts.maintain import (
            MAINTAIN_SECTION_ATTRS_PROMPT,
            MAINTAIN_USER_ATTRS_PROMPT,
        )

        attrs = self.section_as_dict()
        attrs_text = (
            "\n".join(f"{k}: {v}" for k, v in attrs.items()) if attrs else "（空）"
        )
        messages = MAINTAIN_SECTION_ATTRS_PROMPT.format_messages(
            attrs_text=attrs_text,
            history_text=self._history_text(history) or "（空）",
        )
        run_tool_loop(
            messages,
            [self.as_batch_add_section_tool()],
            temperature=settings.llm_generate_temperature,
            max_rounds=4,
        )

        create_turns = list(insight_create_turns or [])
        if not create_turns:
            return
        create_msgs: list[Any] = []
        for item in create_turns:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                create_msgs.extend(list(item))
            else:
                create_msgs.append(item)
        user_attrs = self.as_dict()
        user_text = (
            "\n".join(f"{k}: {v}" for k, v in user_attrs.items())
            if user_attrs
            else "（空）"
        )
        section_text = (
            "\n".join(f"{k}: {v}" for k, v in self.section_as_dict().items())
            if self._section_attrs
            else "（空）"
        )
        user_messages = MAINTAIN_USER_ATTRS_PROMPT.format_messages(
            user_attrs_text=user_text,
            section_attrs_text=section_text,
            history_text=self._history_text(create_msgs) or "（空）",
        )
        run_tool_loop(
            user_messages,
            [self.as_batch_add_tool()],
            temperature=settings.llm_generate_temperature,
            max_rounds=4,
        )

    def total_maintain(
        self,
        turns: list[Any],
        *,
        insight_create_turns: list[Any] | None = None,
        on_done: Any = None,
    ) -> None:
        """三小方法并行；结束仅回调 on_done（不写主对象 / 不 save）。"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        history: list[Any] = []
        for item in turns:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                history.extend(list(item))
            else:
                history.append(item)
        try:
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = [
                    pool.submit(self.maintain_review, history),
                    pool.submit(self.maintain_facts, history),
                    pool.submit(
                        self.maintain_section_attrs,
                        history,
                        insight_create_turns=insight_create_turns,
                    ),
                ]
                for fut in as_completed(futures):
                    fut.result()
        except Exception:
            logger.exception(
                "total_maintain failed uuid=%s section_id=%s",
                self.uuid,
                self.section_id,
            )
        finally:
            if callable(on_done):
                try:
                    on_done()
                except Exception:
                    logger.exception("total_maintain on_done failed")

    # ── 文档加载 / 检索 ───────────────────────────────────────

    def load_file(self, relative_path: str) -> dict[str, Any]:
        """加载相对 tjll 的本地文件：记入文件名列表 → 解析切块 → 入库。"""
        source_file = normalize_backend_path(relative_path)
        if not source_file:
            raise ValueError(f"path must be under ./backend/: {relative_path}")
        path = resolve_repo_path(source_file)
        if not path.is_file():
            raise FileNotFoundError(f"文件不存在: {path}")

        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTS:
            raise ValueError(f"不支持的文件类型: {ext}")

        if source_file not in self._filenames:
            self._filenames.append(source_file)

        text = clean_text(load_document_as_text(str(path)))
        chunks = (
            split_text_to_chunks(
                text,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            if text
            else []
        )
        chunks = [c for c in chunks if c.strip()]
        success, errors = index_section_document_chunks(
            self.uuid,
            self.section_id,
            source_file,
            chunks,
            ensure=True,
        )
        logger.info(
            "load_file uuid=%s section_id=%s file=%s chunks=%d",
            self.uuid,
            self.section_id,
            source_file,
            len(chunks),
        )
        return {
            "source_file": source_file,
            "chunks": len(chunks),
            "success": success,
            "errors": errors,
            "filenames": self.filenames(),
        }

    def search_documents(
        self,
        query: str,
        *,
        filename: str | None = None,
        top_n: int | None = None,
    ) -> list[str]:
        """检索本会话上传文档切块；可选按 filename（source_file）过滤。"""
        if filename is not None:
            name = filename.strip()
            if not name or name not in self._filenames:
                return []
        return search_section_document_texts(
            query,
            uuid=self.uuid,
            section_id=self.section_id,
            filename=filename,
            top_n=top_n,
        )
