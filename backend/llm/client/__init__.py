"""LLM 客户端封装。"""

from backend.llm.client.llm import (
    get_llm,
    get_llm_with_tools,
)

__all__ = [
    "get_llm",
    "get_llm_with_tools",
]
