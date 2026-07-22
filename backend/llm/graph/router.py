"""条件边路由。"""

from __future__ import annotations

from typing import Literal

from backend.llm.graph.state import AskState
from backend.llm.rephrase.rewrite import has_history


def route_after_history(
    state: AskState,
) -> Literal["rewrite", "retrieve_rerank"]:
    """有可用对话历史则走重述，否则直接检索。"""
    if has_history(state.get("history")):
        return "rewrite"
    return "retrieve_rerank"
