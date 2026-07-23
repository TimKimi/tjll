"""AI 路由：对接 backend.llm 门面。

所有端点以 rag-llm.md 定义为准，
chat / recommend / review-summary / generate-review 已废弃，不再提供。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user
from backend.database import get_db
from backend.llm import (
    ask as llm_ask,
    create_ask_interrupt,
    delete_all_insights,
    delete_ask_histories_by_uuid,
    delete_ask_history,
    delete_section_insight,
    delete_user_insight,
    get_ask_history,
    get_section_insight,
    get_user_insight,
    load_section_document,
    release_ask_session,
    release_ask_sessions_by_uuid,
    submit_ask_interrupt,
)
from backend.schemas.common import ApiResponse
from backend.schemas.llm import AskChatRequest, AskInterruptSubmitRequest
from backend.services.llm import LlmService

router = APIRouter(prefix="/api/ai", tags=["AI 助手"])


# ═══════════════════════════════════════════════════════════
# 核心 Ask 流式对话
# ═══════════════════════════════════════════════════════════


@router.post(
    "/ask",
    summary="AI 流式对话",
)
async def ai_ask(
    req: AskChatRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """与 AI 对话，基于 rag-llm.md 定义的 ask 接口。

    用户全局配置（insight_create / insight_use）作为默认值，
    请求参数可覆盖。流式返回 text/plain，非流式返回 JSON。
    """
    service = LlmService(db)
    ask_req = await service.prepare_ask_request(
        query=req.query,
        section_id=req.section_id,
        user=user,
        insight_create=req.insight_create,
        insight_use=req.insight_use,
    )
    stream = llm_ask(ask_req)

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
    """按 uuid + section_id 返回完整会话历史。"""
    try:
        result = get_ask_history(uuid=user["sub"], section_id=section_id)
        return ApiResponse.ok(data=result.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/history",
    summary="删除单条会话历史",
)
async def ai_delete_history(
    section_id: str = Query(..., description="会话 ID"),
    user: dict = Depends(get_current_user),
):
    """删除指定 uuid + section_id 的会话历史。"""
    try:
        result = delete_ask_history(uuid=user["sub"], section_id=section_id)
        return ApiResponse.ok(data=result.model_dump(), message="已删除")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/histories",
    summary="删除用户全部会话历史",
)
async def ai_delete_histories(
    user: dict = Depends(get_current_user),
):
    """删除当前用户下的全部会话历史（内存 + Redis）。"""
    try:
        result = delete_ask_histories_by_uuid(uuid=user["sub"])
        return ApiResponse.ok(data=result.model_dump(), message="已删除")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════
# 会话池管理
# ═══════════════════════════════════════════════════════════


@router.post(
    "/session/release",
    summary="释放会话槽",
)
async def ai_release_session(
    section_id: str | None = Query(None, description="会话 ID（不传则释放全部）"),
    user: dict = Depends(get_current_user),
):
    """释放当前用户单个或全部会话槽（不删 Redis 历史）。"""
    uuid = user["sub"]
    if section_id:
        release_ask_session(uuid=uuid, section_id=section_id)
        return ApiResponse.ok(message="会话已释放")
    result = release_ask_sessions_by_uuid(uuid=uuid)
    return ApiResponse.ok(data=result.model_dump(), message="会话已释放")


# ═══════════════════════════════════════════════════════════
# 洞察（占位，后续接入真实实现）
# ═══════════════════════════════════════════════════════════


@router.get("/insight/user", summary="获取用户洞察")
async def ai_get_user_insight(user: dict = Depends(get_current_user)):
    result = get_user_insight(uuid=user["sub"])
    return ApiResponse.ok(data=result.model_dump())


@router.get("/insight/section", summary="获取会话洞察")
async def ai_get_section_insight(
    section_id: str = Query(...),
    user: dict = Depends(get_current_user),
):
    result = get_section_insight(uuid=user["sub"], section_id=section_id)
    return ApiResponse.ok(data=result.model_dump())


@router.delete("/insight/user", summary="删除用户洞察")
async def ai_delete_user_insight(user: dict = Depends(get_current_user)):
    result = delete_user_insight(uuid=user["sub"])
    return ApiResponse.ok(data=result.model_dump())


@router.delete("/insight/section", summary="删除会话洞察")
async def ai_delete_section_insight(
    section_id: str = Query(...),
    user: dict = Depends(get_current_user),
):
    result = delete_section_insight(uuid=user["sub"], section_id=section_id)
    return ApiResponse.ok(data=result.model_dump())


@router.delete("/insight/all", summary="删除全部洞察")
async def ai_delete_all_insights(user: dict = Depends(get_current_user)):
    result = delete_all_insights(uuid=user["sub"])
    return ApiResponse.ok(data=result.model_dump())


# ═══════════════════════════════════════════════════════════
# 文档处理（占位）
# ═══════════════════════════════════════════════════════════


@router.post("/document", summary="加载会话文档")
async def ai_load_document(
    section_id: str = Query(...),
    file_path: str = Query(...),
    user: dict = Depends(get_current_user),
):
    result = load_section_document(
        {"uuid": user["sub"], "section_id": section_id, "file_path": file_path}
    )
    return ApiResponse.ok(data=result.model_dump())


# ═══════════════════════════════════════════════════════════
# Ask interrupt 澄清问答（占位）
# ═══════════════════════════════════════════════════════════


@router.post("/interrupt/create", summary="创建澄清问答")
async def ai_create_interrupt(
    section_id: str = Query(...),
    query: str = Query(...),
    user: dict = Depends(get_current_user),
):
    result = create_ask_interrupt(
        {"uuid": user["sub"], "section_id": section_id, "query": query}
    )
    return ApiResponse.ok(data=result.model_dump())


@router.post("/interrupt/submit", summary="提交澄清答案")
async def ai_submit_interrupt(
    body: AskInterruptSubmitRequest,
    user: dict = Depends(get_current_user),
):
    result = submit_ask_interrupt(body.model_dump())
    return ApiResponse.ok(data=result.model_dump())
