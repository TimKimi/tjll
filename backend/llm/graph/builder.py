"""组装 Ask 图：节点、条件边、RedisSaver；会话池挂载共享 compiled 图。"""

from __future__ import annotations

import logging
from typing import Any, cast

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.redis import RedisSaver
from langgraph.graph import END, START, StateGraph

from backend.config import settings
from backend.llm.graph import nodes
from backend.llm.graph.router import (
    route_after_attachment,
    route_after_enrich,
    route_after_user_insight,
)
from backend.llm.graph.session_pool import AskSession, get_session_pool
from backend.llm.graph.state import AskState

logger = logging.getLogger("backend.llm.graph.builder")

_compiled: Any | None = None
_checkpointer: BaseCheckpointSaver | None = None


def create_redis_checkpointer(redis_url: str | None = None) -> RedisSaver:
    """创建并 setup RedisSaver（进程内可复用）。"""
    url = redis_url or settings.redis_url
    saver = RedisSaver(redis_url=url)
    saver.setup()
    logger.info("RedisSaver setup ok")
    return saver


def build_ask_graph(
    *,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """构建并 compile Ask 图（至 retrieve；生成与刷历史在 service 侧）。"""
    # cast: ty/langgraph StateT bound 与 typing.TypedDict(total=False) 推断不完全兼容
    graph = StateGraph(cast(Any, AskState))
    graph.add_node("prepare", nodes.prepare)
    graph.add_node("fetch_attachments", nodes.fetch_attachments)
    graph.add_node("fetch_user_insight", nodes.fetch_user_insight)
    graph.add_node("fetch_section_insight", nodes.fetch_section_insight)
    graph.add_node("rewrite", nodes.rewrite)
    graph.add_node("retrieve_rerank", nodes.retrieve_rerank)

    graph.add_edge(START, "prepare")
    graph.add_conditional_edges(
        "prepare",
        route_after_attachment,
        {
            "fetch_attachments": "fetch_attachments",
            "fetch_user_insight": "fetch_user_insight",
            "fetch_section_insight": "fetch_section_insight",
        },
    )
    graph.add_conditional_edges(
        "fetch_attachments",
        route_after_user_insight,
        {
            "fetch_user_insight": "fetch_user_insight",
            "fetch_section_insight": "fetch_section_insight",
        },
    )
    graph.add_edge("fetch_user_insight", "fetch_section_insight")
    graph.add_conditional_edges(
        "fetch_section_insight",
        route_after_enrich,
        {
            "rewrite": "rewrite",
            "retrieve_rerank": "retrieve_rerank",
        },
    )
    graph.add_edge("rewrite", "retrieve_rerank")
    graph.add_edge("retrieve_rerank", END)

    cp = checkpointer if checkpointer is not None else create_redis_checkpointer()
    return graph.compile(checkpointer=cp)


def _ensure_shared_graph(
    *,
    checkpointer: BaseCheckpointSaver | None = None,
    force_reload: bool = False,
) -> Any:
    global _compiled, _checkpointer
    pool = get_session_pool()
    if _compiled is not None and not force_reload:
        return _compiled
    _checkpointer = (
        checkpointer if checkpointer is not None else create_redis_checkpointer()
    )
    _compiled = build_ask_graph(checkpointer=_checkpointer)
    pool.set_shared_graph(_compiled, _checkpointer)
    return _compiled


def get_ask_graph(
    uuid: str | None = None,
    section_id: str | None = None,
    *,
    force_reload: bool = False,
    checkpointer: BaseCheckpointSaver | None = None,
) -> Any:
    """取共享 compiled 图；若同时传入 uuid 与 section_id 则绑定会话池。

    仅返回共享图时可不传 id；创建/绑定会话时 **uuid 与 section_id 必须都有**。
    """
    graph = _ensure_shared_graph(checkpointer=checkpointer, force_reload=force_reload)
    if uuid is None and section_id is None:
        return graph
    if not uuid or not section_id:
        raise ValueError("uuid and section_id are both required to bind a session")
    session = get_session_pool().get_or_create(uuid, section_id)
    session.graph = graph
    return session.graph


def get_ask_session(
    uuid: str,
    section_id: str,
    *,
    checkpointer: BaseCheckpointSaver | None = None,
) -> AskSession:
    """申请/复用会话槽（含内存 history）；uuid 与 section_id 均必填。"""
    _ensure_shared_graph(checkpointer=checkpointer)
    return get_session_pool().get_or_create(uuid, section_id)


def release_ask_session(uuid: str, section_id: str) -> None:
    """显式释放会话并刷 Redis 历史；uuid 与 section_id 均必填。"""
    get_session_pool().release(uuid, section_id)


def reset_ask_graph_cache() -> None:
    """测试用：清空单例与会话池（不刷 Redis）。"""
    global _compiled, _checkpointer
    _compiled = None
    _checkpointer = None
    get_session_pool().reset()
    from backend.llm.insight.registry import get_insight_registry

    get_insight_registry().reset()
