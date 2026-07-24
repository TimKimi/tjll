"""AI 路由：流式对话 + 会话管理。

对外暴露：
  - POST   /api/ai/ask                          AI 流式对话
  - GET    /api/ai/history?section_id=          获取会话历史
  - POST   /api/ai/session/refresh?section_id=  刷新会话（释放槽位 + 重载历史）
  - GET    /api/ai/section/reviews?section_ids= 批量获取会话摘要
  - DELETE /api/ai/history?section_id=          删除单个会话（历史 + 文件）
  - DELETE /api/ai/histories                    删除全部会话（历史 + 文件）
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.core.dependencies import get_current_user
from backend.llm import (
    AskInterruptResult,
    AskParams,
    AskStream,
    ask as llm_ask,
    delete_ask_histories_by_uuid,
    delete_ask_history,
    get_ask_history,
    get_section_facts,
    get_section_insight,
    get_section_review,
    release_ask_session,
    set_section_review,
    update_section_facts,
)
from backend.schemas.ai import AskChatRequest
from backend.schemas.common import ApiResponse
from backend.services.file import FileService

logger = logging.getLogger("backend.routers.ai")
router = APIRouter(prefix="/api/ai", tags=["AI 助手"])


# ═══════════════════════════════════════════════════════════
# 流式对话
# ═══════════════════════════════════════════════════════════


@router.post(
    "/ask",
    summary="AI 流式对话",
)
async def ai_ask(
    req: AskChatRequest,
    user: dict = Depends(get_current_user),
):
    """与 AI 对话。

    流式返回 ``text/plain``，非流式返回 JSON。
    ``uuid`` 由后端从 JWT 自动注入，前端无需传入。
    """
    ask_params = AskParams(
        query=req.query,
        section_id=req.section_id,
        uuid=user["sub"],
        docx=req.docx,
        doc=req.doc,
        txt=req.txt,
        md=req.md,
        pdf=req.pdf,
        images=req.images,
        insight_create=req.insight_create,
        insight_use=req.insight_use,
    )
    out = llm_ask(ask_params)

    # rewrite HITL：问卷非流式 JSON 返回（与 AskStream 区分）
    if isinstance(out, AskInterruptResult):
        return ApiResponse.ok(data=out.model_dump())

    stream: AskStream = out
    if not req.stream:
        "".join(stream)
        resp = stream.response
        if resp is None:
            raise HTTPException(status_code=500, detail="AI 响应生成失败")
        return ApiResponse.ok(data=resp.model_dump())

    return StreamingResponse(stream, media_type="text/plain")


# ═══════════════════════════════════════════════════════════
# 会话历史
# ═══════════════════════════════════════════════════════════


@router.get(
    "/history",
    summary="获取会话历史",
)
async def ai_get_history(
    section_id: str = Query(..., description="会话 ID"),
    user: dict = Depends(get_current_user),
):
    """按 ``section_id`` 返回该会话的完整聊天历史。"""
    try:
        result = get_ask_history(uuid=user["sub"], section_id=section_id)
        return ApiResponse.ok(data=result.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════
# 刷新会话（合并操作）
# ═══════════════════════════════════════════════════════════


@router.post(
    "/session/refresh",
    summary="刷新会话（释放槽位 + 重载历史）",
)
async def ai_refresh_session(
    section_id: str = Query(..., description="会话 ID"),
    user: dict = Depends(get_current_user),
):
    """刷新会话：先释放内存会话槽，再重新加载历史。"""
    uuid = user["sub"]
    try:
        release_ask_session(uuid=uuid, section_id=section_id)
        history = get_ask_history(uuid=uuid, section_id=section_id)
        return ApiResponse.ok(data=history.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════
# 批量获取会话摘要
# ═══════════════════════════════════════════════════════════


@router.get(
    "/section/reviews",
    summary="批量获取会话摘要",
)
async def ai_section_reviews(
    section_ids: str = Query(..., description="逗号分隔的多个 section_id"),
    user: dict = Depends(get_current_user),
):
    """批量获取左侧栏各会话的摘要预览。"""
    uuid = user["sub"]
    ids = [sid.strip() for sid in section_ids.split(",") if sid.strip()]
    reviews: dict[str, str] = {}
    for section_id in ids:
        try:
            review = get_section_review(uuid=uuid, section_id=section_id)
            reviews[section_id] = review or ""
        except Exception:
            reviews[section_id] = ""
    return ApiResponse.ok(data={"reviews": reviews})


# ═══════════════════════════════════════════════════════════
# 会话详情
# ═══════════════════════════════════════════════════════════


@router.get(
    "/session/detail",
    summary="获取会话详情（facts + review + insight）",
)
async def ai_session_detail(
    section_id: str = Query(..., description="会话 ID"),
    user: dict = Depends(get_current_user),
):
    """合并返回会话的 facts、review 和 insight，用于详情弹窗展示。"""
    uuid = user["sub"]
    facts = get_section_facts(uuid=uuid, section_id=section_id)
    review = get_section_review(uuid=uuid, section_id=section_id)
    insight = get_section_insight(uuid=uuid, section_id=section_id)
    return ApiResponse.ok(
        data={
            "facts": facts or [],
            "review": review or "",
            "insight": insight or {},
        }
    )


@router.put(
    "/section/facts",
    summary="更新会话 facts",
)
async def ai_update_facts(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """更新会话 facts 列表。

    body 格式: ``{ "section_id": "...", "items": ["fact1", "fact2", ...] }``
    """
    section_id = body.get("section_id")
    items = body.get("items", [])
    if not section_id:
        raise HTTPException(status_code=400, detail="section_id is required")
    update_section_facts(uuid=user["sub"], section_id=section_id, items=items)
    return ApiResponse.ok(message="已更新")


@router.put(
    "/section/review",
    summary="更新会话 review",
)
async def ai_update_review(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """更新会话 review 文本。

    body 格式: ``{ "section_id": "...", "text": "..." }``
    """
    section_id = body.get("section_id")
    text = body.get("text", "")
    if not section_id:
        raise HTTPException(status_code=400, detail="section_id is required")
    set_section_review(uuid=user["sub"], section_id=section_id, text=text)
    return ApiResponse.ok(message="已更新")


# ═══════════════════════════════════════════════════════════
# 删除会话
# ═══════════════════════════════════════════════════════════


@router.delete(
    "/history",
    summary="删除单个会话（历史 + 文件）",
)
async def ai_delete_history(
    section_id: str = Query(..., description="会话 ID"),
    user: dict = Depends(get_current_user),
):
    """删除指定会话：
    1. 清空 Redis 聊天历史
    2. 删除上传的附件目录
    """
    uuid = user["sub"]
    try:
        delete_ask_history(uuid=uuid, section_id=section_id)

        FileService.delete_session_files(
            username=user.get("username", ""),
            section_id=section_id,
        )

        return ApiResponse.ok(message="会话已删除")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/histories",
    summary="删除全部会话（历史 + 文件）",
)
async def ai_delete_histories(
    user: dict = Depends(get_current_user),
):
    """删除当前用户的所有会话：
    1. 清空所有 Redis 聊天历史
    2. 删除所有上传的附件目录
    """
    uuid = user["sub"]
    result = delete_ask_histories_by_uuid(uuid=uuid)

    FileService.delete_all_user_files(username=user.get("username", ""))

    return ApiResponse.ok(
        data=result.model_dump() if hasattr(result, "model_dump") else None,
        message="全部会话已删除",
    )
