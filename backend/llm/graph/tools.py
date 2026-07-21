"""图节点辅助工具（结果不进入 AskState）。"""

from __future__ import annotations

from typing import Any

from langchain_core.documents import Document
from langchain_core.tools import tool


def sources_from_docs(docs: list[Document]) -> list[dict[str, Any]]:
    """将精排 Document 转为对外 sources 结构（无 embedding）。

    供 retrieve 节点调用；结果应写入 AskSession 侧车，而不是 State。
    """
    out: list[dict[str, Any]] = []
    for doc in docs:
        out.append(
            {
                "content": doc.page_content,
                "metadata": {
                    k: v for k, v in dict(doc.metadata).items() if k != "embedding"
                },
            }
        )
    return out


@tool("build_rag_sources")
def build_rag_sources_tool(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """LangChain tool 形态：从已有 chunk dict 生成 sources（去 embedding）。

    ``chunks`` 每项需含 ``content`` 与可选 ``metadata``。
    """
    out: list[dict[str, Any]] = []
    for item in chunks:
        meta = dict(item.get("metadata") or {})
        meta.pop("embedding", None)
        out.append({"content": str(item.get("content") or ""), "metadata": meta})
    return out
