"""用户洞察：多数据属性 + 拼成长文 + 切割入库 + 检索（RAG 能力仅调用）。"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import StructuredTool

from backend.config import settings
from backend.rag.document.chunking import split_text_to_chunks
from backend.rag.document.indexing import (
    delete_insight_from_opensearch,
    index_insight_chunks,
)
from backend.rag.retrieve.search import search_insight_text

logger = logging.getLogger("backend.llm.insight.model")

_SEGMENT_SEP = "\n\n\n"
_ATTR_SEP = "\n"


def format_attr_line(key: str, value: str) -> str:
    """单条数据属性的标准表述。"""
    return f"用户的【{key}】是：【{value}】"


class UserInsight:
    """按 uuid 绑定的用户洞察（内存数据属性 + OpenSearch chunk）。"""

    def __init__(self, uuid: str) -> None:
        text = (uuid or "").strip()
        if not text:
            raise ValueError("uuid is required")
        self.uuid = text
        self._attrs: dict[str, str] = {}
        self.last_chunk_size: int = 0
        self.max_attr_len: int = 0

    def as_dict(self) -> dict[str, str]:
        """数据属性视图（副本）。"""
        return dict(self._attrs)

    def _recompute_max_attr_len(self) -> None:
        if not self._attrs:
            self.max_attr_len = 0
            return
        self.max_attr_len = max(
            len(format_attr_line(k, v)) for k, v in self._attrs.items()
        )

    def batch_add(self, attrs: dict[str, Any]) -> dict[str, str]:
        """批量添加/覆盖数据属性；返回当前全部属性。"""
        if not isinstance(attrs, dict):
            raise TypeError("attrs must be a dict")
        for key, value in attrs.items():
            k = str(key).strip()
            if not k:
                continue
            self._attrs[k] = "" if value is None else str(value)
        self._recompute_max_attr_len()
        logger.info(
            "batch_add uuid=%s attrs=%d max_attr_len=%d",
            self.uuid,
            len(self._attrs),
            self.max_attr_len,
        )
        return self.as_dict()

    def as_batch_add_tool(self) -> StructuredTool:
        """供 LLM ``bind_tools`` / ``invoke_with_tools`` 调用的批量添加工具。"""

        def _tool(attrs: dict[str, Any]) -> dict[str, str]:
            """批量写入用户洞察数据属性。

            Args:
                attrs: 键值对字典，例如 ``{"喜欢的菜": "火锅", "忌口": "香菜"}``。
            """
            return self.batch_add(attrs)

        return StructuredTool.from_function(
            func=_tool,
            name="batch_add_insight_attrs",
            description=(
                "批量添加或更新用户洞察数据属性。"
                "参数 attrs 为字典，键为属性名，值为属性内容。"
            ),
        )

    def to_long_text(self, size: int | None = None) -> str:
        """将全部数据属性按段长规则拼成长文（段间 ``\\n\\n\\n``）。"""
        if not self._attrs:
            return ""

        requested = settings.insight_chunk_size if size is None else int(size)
        if requested < 1:
            requested = 1
        # 若传入上限小于最长单条属性，则改用 max_attr_len，保证属性可完整存在
        limit = (
            self.max_attr_len
            if self.max_attr_len > 0 and requested < self.max_attr_len
            else requested
        )
        if limit < 1:
            limit = 1

        parts: list[str] = []
        for key, value in self._attrs.items():
            parts.append(format_attr_line(key, value))

        out = ""
        # 当前段长度：自上一个 \n\n\n 之后（即当前段内字符数）
        segment_len = 0
        for piece in parts:
            if segment_len == 0:
                # 新段起点，直接写入
                if out:
                    out += _SEGMENT_SEP
                out += piece
                segment_len = len(piece)
                continue
            # 尝试用 \n 接到当前段
            addition = _ATTR_SEP + piece
            if segment_len + len(addition) <= limit:
                out += addition
                segment_len += len(addition)
            else:
                out += _SEGMENT_SEP + piece
                segment_len = len(piece)
        return out

    def split_and_store(self) -> int:
        """按配置长度拼文 → 仅按 ``\\n\\n\\n`` 切割 → 写入 OpenSearch。"""
        text = self.to_long_text(settings.insight_chunk_size)
        if not text.strip():
            if self.last_chunk_size > 0:
                delete_insight_from_opensearch(self.uuid)
                self.last_chunk_size = 0
            return 0

        # chunk_size 取全文长度，避免次级字符切割；只认 \n\n\n
        chunks = split_text_to_chunks(
            text,
            chunk_size=max(len(text), 1),
            chunk_overlap=0,
            separators=[_SEGMENT_SEP],
        )
        chunks = [c for c in chunks if c.strip()]
        n = len(chunks)

        if 0 < n < self.last_chunk_size:
            delete_insight_from_opensearch(self.uuid)

        index_insight_chunks(self.uuid, chunks, ensure=True)
        self.last_chunk_size = n
        logger.info(
            "split_and_store uuid=%s chunks=%d last_chunk_size=%d",
            self.uuid,
            n,
            self.last_chunk_size,
        )
        return n

    def search(self, query: str) -> str:
        """混合检索 + 精排，返回本 uuid 下最优一条 chunk 的 text。"""
        if self.last_chunk_size <= 0:
            return ""
        return search_insight_text(query, uuid=self.uuid)

    def save_to_redis(self) -> None:
        """持久化用户洞察到 Redis。"""
        from backend.llm.insight.store import save_user_insight

        save_user_insight(self)

    @classmethod
    def load_from_redis(cls, uuid: str) -> UserInsight | None:
        """从 Redis 加载；不存在返回 None。"""
        from backend.llm.insight.store import load_user_insight

        return load_user_insight(uuid)


def make_batch_add_tool(insight: UserInsight) -> StructuredTool:
    """模块级工厂：为指定 ``UserInsight`` 生成批量添加工具。"""
    return insight.as_batch_add_tool()
