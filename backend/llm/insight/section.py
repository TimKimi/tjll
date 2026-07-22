"""会话洞察：继承 UserInsight，增加会话属性 / facts / review / 文档切块。"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import StructuredTool

from backend.config import settings
from backend.llm.insight.model import UserInsight, format_attr_line
from backend.rag.document.chunking import split_text_to_chunks
from backend.rag.document.clean import clean_text
from backend.rag.document.indexing import (
    delete_section_insight_from_opensearch,
    index_section_document_chunks,
    index_section_insight_chunks,
)
from backend.rag.document.loaders import load_document_as_text
from backend.rag.document.paths import (
    SUPPORTED_EXTS,
    resolve_repo_path,
    to_repo_relative_posix,
)
from backend.rag.retrieve.search import (
    search_section_document_texts,
    search_section_insight_text,
)

logger = logging.getLogger("backend.llm.insight.section")

_SEGMENT_SEP = "\n\n\n"
_ATTR_SEP = "\n"


class SectionInsight(UserInsight):
    """按 uuid + section_id 绑定的会话洞察。

    - 父类 ``_attrs`` / ``search`` / ``split_and_store``：用户级洞察（不变）
    - ``_section_attrs``：本会话独有属性（独立索引）
    - ``_filenames`` / 文档索引：上传文件切块
    - ``_facts`` / ``_review``：仅内存
    """

    def __init__(self, uuid: str, section_id: str) -> None:
        super().__init__(uuid)
        sid = (section_id or "").strip()
        if not sid:
            raise ValueError("section_id is required")
        self.section_id = sid
        self._filenames: list[str] = []
        self._section_attrs: dict[str, str] = {}
        self._facts: list[str] = []
        self._review: str = ""
        self.last_section_chunk_size: int = 0
        self.max_section_attr_len: int = 0

    # ── 文档名列表 ────────────────────────────────────────────

    def filenames(self) -> list[str]:
        return list(self._filenames)

    # ── 会话属性（对齐父类 _attrs）────────────────────────────

    def section_as_dict(self) -> dict[str, str]:
        return dict(self._section_attrs)

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
        logger.info(
            "batch_add_section uuid=%s section_id=%s attrs=%d",
            self.uuid,
            self.section_id,
            len(self._section_attrs),
        )
        return self.section_as_dict()

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
        """检索本会话属性切块（混合 + 精排，返回最优一条）。"""
        return search_section_insight_text(
            query, uuid=self.uuid, section_id=self.section_id
        )

    # ── facts ────────────────────────────────────────────────

    def get_facts(self) -> list[str]:
        return list(self._facts)

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
        cleaned = [str(x) for x in items]

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

    def set_review(self, text: str) -> str:
        self._review = "" if text is None else str(text)
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

    # ── 文档加载 / 检索 ───────────────────────────────────────

    def load_file(self, relative_path: str) -> dict[str, Any]:
        """加载相对 tjll 的本地文件：记入文件名列表 → 解析切块 → 入库。"""
        path = resolve_repo_path(relative_path)
        if not path.is_file():
            raise FileNotFoundError(f"文件不存在: {path}")

        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTS:
            raise ValueError(f"不支持的文件类型: {ext}")

        source_file = to_repo_relative_posix(path)
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
        return search_section_document_texts(
            query,
            uuid=self.uuid,
            section_id=self.section_id,
            filename=filename,
            top_n=top_n,
        )
