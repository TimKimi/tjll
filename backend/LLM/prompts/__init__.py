"""Prompt 模板。"""

from backend.LLM.prompts.rag import RAG_PROMPT, RAG_PROMPT_WITH_HISTORY
from backend.LLM.prompts.rephrase import REPHRASE_PROMPT

__all__ = [
    "RAG_PROMPT",
    "RAG_PROMPT_WITH_HISTORY",
    "REPHRASE_PROMPT",
]
