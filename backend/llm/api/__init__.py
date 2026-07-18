"""LLM 对外门面（其他后端模块请只依赖本包，勿直接 import backend.rag）。"""

from backend.llm.api.handler import ask
from backend.llm.api.schemas import AskRequest, AskResponse, RagSnippet

__all__ = [
    "AskRequest",
    "AskResponse",
    "RagSnippet",
    "ask",
]
