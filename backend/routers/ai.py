"""AI 路由：流式对话 + 会话管理。

对外暴露：
  - POST   /api/ai/ask                     AI 流式对话
  - GET    /api/ai/history?section_id=     获取会话历史
  - DELETE /api/ai/history?section_id=     删除单个会话（历史 + 文件）
  - DELETE /api/ai/histories               删除全部会话（历史 + 文件）
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.core.dependencies import get_current_user
from backend.llm import (
    AskParams,
    ask as llm_ask,
    delete_ask_histories_by_uuid,
    delete_ask_history,
    get_ask_history,
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
    stream = llm_ask(ask_params)

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
        # 清 Redis 历史
        delete_ask_history(uuid=uuid, section_id=section_id)

        # 删除附件文件
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

    # 删除所有附件
    FileService.delete_all_user_files(username=user.get("username", ""))

    return ApiResponse.ok(
        data=result.model_dump() if hasattr(result, "model_dump") else None,
        message="全部会话已删除",
    )
