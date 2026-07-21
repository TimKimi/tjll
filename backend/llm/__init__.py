"""LLM 模块：客户端封装 + LangGraph ask 门面 + RAG 管线。

其他后端模块推荐只使用::

    from backend.llm import ask, AskRequest, AskResponse

不要直接依赖 ``backend.rag``。
"""

from backend.llm.client.llm import (
    get_llm,
    get_llm_with_tools,
    invoke_chat,
    invoke_llm,
    invoke_with_tools,
    stream_chat,
    stream_llm,
    stream_with_tools,
)
from backend.llm.graph import AskStream, ask, release_ask_session
from backend.llm.pipeline.rag_pipeline import (
    RagAnswer,
    answer_query,
    answer_query_with_sources,
    stream_answer_query,
)
from backend.llm.schemas import AskRequest, AskResponse, HistoryMessage, RagSnippet

__all__ = [
    # 推荐：协作方门面（LangGraph 流式 ask）
    "AskRequest",
    "AskResponse",
    "AskStream",
    "HistoryMessage",
    "RagSnippet",
    "ask",
    "release_ask_session",
    # 进阶 / 内部
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
