"""LLM 模块：客户端封装 + RAG 会话一条龙（对齐 backend.RAG 分子目录风格）。"""

from backend.LLM.client.llm import (
    get_llm,
    get_llm_with_tools,
    invoke_chat,
    invoke_llm,
    invoke_with_tools,
    stream_chat,
    stream_llm,
    stream_with_tools,
)
from backend.LLM.pipeline.rag_pipeline import (
    RagAnswer,
    answer_query,
    answer_query_with_sources,
    stream_answer_query,
)

__all__ = [
    "RagAnswer",
    "answer_query",
    "answer_query_with_sources",
    "get_llm",
    "get_llm_with_tools",
    "invoke_chat",
    "invoke_llm",
    "invoke_with_tools",
    "stream_answer_query",
    "stream_chat",
    "stream_llm",
    "stream_with_tools",
]
