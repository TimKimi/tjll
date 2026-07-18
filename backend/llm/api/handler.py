"""面向其他后端模块的 ask 门面：只处理 query + section_id。"""

from __future__ import annotations

from typing import Any

from backend.llm.api.schemas import AskRequest, AskResponse, RagSnippet
from backend.llm.pipeline.rag_pipeline import answer_query_with_sources


def ask(req: AskRequest | dict[str, Any]) -> AskResponse:
    """同进程入口：历史 → 重述 → 混合检索 → 重排 → LLM → 存历史。

    其他后端请只调用本函数（或 ``from backend.llm import ask``），
    不要直接依赖 ``backend.rag``。

    附件字段（docx/doc/md/pdf/images）可出现在入参中，本阶段忽略。
    """
    request = req if isinstance(req, AskRequest) else AskRequest.model_validate(req)
    result = answer_query_with_sources(request.query, request.section_id)
    sources = [
        RagSnippet(
            content=str(item.get("content") or ""),
            metadata=dict(item.get("metadata") or {}),
        )
        for item in result.sources
    ]
    return AskResponse(
        query=result.query,
        section_id=result.section_id,
        uuid=request.uuid,
        answer=result.answer,
        sources=sources,
    )
