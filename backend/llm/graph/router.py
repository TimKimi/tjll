"""条件边路由。"""

from __future__ import annotations

from typing import Literal

from backend.llm.graph.session_pool import session_history
from backend.llm.graph.state import AskState
from backend.llm.rephrase.rewrite import needs_rewrite


def route_after_attachment(
    state: AskState,
) -> Literal["fetch_attachments", "fetch_user_insight", "fetch_section_insight"]:
    """有附件路径则查文档；否则按 insight_use 进入用户/会话属性节点。"""
    names = [x for x in (state.get("attachment_filenames") or []) if str(x).strip()]
    if names:
        return "fetch_attachments"
    if bool(state.get("insight_use")):
        return "fetch_user_insight"
    return "fetch_section_insight"


def route_after_user_insight(
    state: AskState,
) -> Literal["fetch_user_insight", "fetch_section_insight"]:
    """insight_use 为真则查用户属性，否则直达会话属性节点。"""
    if bool(state.get("insight_use")):
        return "fetch_user_insight"
    return "fetch_section_insight"


def route_after_enrich(
    state: AskState,
) -> Literal["rewrite", "retrieve_rerank"]:
    """insight/attachment 非空或非首轮 → rewrite，否则直接检索。"""
    uuid = (state.get("uuid") or "").strip()
    section_id = (state.get("section_id") or "").strip()
    history = session_history(uuid, section_id) if uuid and section_id else []
    if needs_rewrite(
        history,
        insight=state.get("insight"),
        attachment=state.get("attachment"),
    ):
        return "rewrite"
    return "retrieve_rerank"
