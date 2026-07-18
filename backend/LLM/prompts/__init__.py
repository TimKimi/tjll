"""Prompt 模板。"""

from backend.LLM.prompts.rag import RAG_PROMPT, RAG_PROMPT_WITH_HISTORY
from backend.LLM.prompts.rephrase import REPHRASE_PROMPT
from backend.LLM.prompts.review_clean import (
    EMPTY_DELTA,
    EXTRACT_SYSTEM,
    EXTRACT_USER_TEMPLATE,
    NEGATIVE_MARKER,
    POLISH_SYSTEM,
    POLISH_USER_TEMPLATE,
    POSITIVE_MARKER,
)

__all__ = [
    "RAG_PROMPT",
    "RAG_PROMPT_WITH_HISTORY",
    "REPHRASE_PROMPT",
    "EXTRACT_SYSTEM",
    "EXTRACT_USER_TEMPLATE",
    "POLISH_SYSTEM",
    "POLISH_USER_TEMPLATE",
    "POSITIVE_MARKER",
    "NEGATIVE_MARKER",
    "EMPTY_DELTA",
]
