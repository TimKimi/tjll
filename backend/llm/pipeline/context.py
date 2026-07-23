"""检索上下文格式化（供 LangGraph retrieve 节点使用）。"""

from __future__ import annotations

from langchain_core.documents import Document


def format_docs(docs: list[Document]) -> str:
    parts: list[str] = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("name") or doc.metadata.get("id") or "未知"
        chunk_idx = doc.metadata.get("chunk_index", "-")
        parts.append(
            f"[片段 {i}] （来源：{source}，chunk#{chunk_idx}）\n{doc.page_content}"
        )
    return "\n\n".join(parts)
