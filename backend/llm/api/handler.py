"""面向其他后端模块的 ask 门面：只处理 query + section_id。"""

from __future__ import annotations

import logging
from typing import Any

from backend.llm.api.schemas import (
    AskRequest,
    AskResponse,
    HistoryMessage,
    RagSnippet,
)
from backend.llm.pipeline.rag_pipeline import answer_query_with_sources
from backend.logging_setup import setup_app_logging

logger = logging.getLogger("backend.llm.api.handler")


def ask(req: AskRequest | dict[str, Any]) -> AskResponse:
    """同进程入口：历史 → 重述 → 混合检索 → 重排 → LLM → 存历史。

    其他后端请只调用本函数（或 ``from backend.llm import ask``），
    不要直接依赖 ``backend.rag``。

    附件字段（docx/doc/md/pdf/images）可出现在入参中，本阶段忽略。
    """
    setup_app_logging()
    request = req if isinstance(req, AskRequest) else AskRequest.model_validate(req)
    logger.info(
        "ask start section_id=%s uuid=%s query_len=%d",
        request.section_id,
        request.uuid,
        len(request.query),
    )
    try:
        result = answer_query_with_sources(request.query, request.section_id)
        sources = [
            RagSnippet(
                content=str(item.get("content") or ""),
                metadata={
                    k: v
                    for k, v in dict(item.get("metadata") or {}).items()
                    if k != "embedding"
                },
            )
            for item in result.sources
        ]
        history = [
            HistoryMessage(role=h["role"], content=h["content"])  # type: ignore[arg-type]
            for h in result.history
        ]
        resp = AskResponse(
            query=result.query,
            section_id=result.section_id,
            uuid=request.uuid,
            answer=result.answer,
            sources=sources,
            history=history,
        )
        logger.info(
            "ask ok section_id=%s sources=%d history=%d answer_len=%d",
            resp.section_id,
            len(resp.sources),
            len(resp.history),
            len(resp.answer),
        )
        return resp
    except Exception:
        logger.exception(
            "ask failed section_id=%s uuid=%s",
            request.section_id,
            request.uuid,
        )
        raise
