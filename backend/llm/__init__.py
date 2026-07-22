"""LLM 模块。

协作入口::

    from backend.llm import ask, get_ask_history, delete_ask_history, AskRequest
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
from backend.llm.graph import (
    AskStream,
    ask,
    delete_ask_histories_by_uuid,
    delete_ask_history,
    get_ask_history,
    release_ask_session,
)
from backend.llm.insight import UserInsight, delete_insight_from_opensearch
from backend.llm.pipeline.rag_pipeline import (
    RagAnswer,
    answer_query,
    answer_query_with_sources,
    stream_answer_query,
)
from backend.llm.schemas import (
    AskRequest,
    AskResponse,
    DeleteHistoryByUuidRequest,
    DeleteHistoryResponse,
    HistoryMessage,
    HistoryRequest,
    HistoryResponse,
    RagSnippet,
)

__all__ = [
    # 门面
    "AskRequest",
    "AskResponse",
    "AskStream",
    "DeleteHistoryByUuidRequest",
    "DeleteHistoryResponse",
    "HistoryMessage",
    "HistoryRequest",
    "HistoryResponse",
    "RagSnippet",
    "UserInsight",
    "ask",
    "delete_ask_histories_by_uuid",
    "delete_ask_history",
    "delete_insight_from_opensearch",
    "get_ask_history",
    "release_ask_session",
    # 管线 / 客户端
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
