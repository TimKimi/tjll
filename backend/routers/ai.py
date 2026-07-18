"""AI 助手路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.ai import (
    ChatRequest,
    ChatResponse,
    GenerateReviewRequest,
    GenerateReviewResponse,
    RecommendRequest,
    RecommendResponse,
    ReviewSummaryRequest,
    ReviewSummaryResponse,
)
from backend.schemas.common import ApiResponse
from backend.services.ai import AIService

router = APIRouter(prefix="/api/ai", tags=["AI 助手"])


@router.post(
    "/chat",
    summary="AI 对话",
    response_model=ApiResponse[ChatResponse],
)
async def ai_chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ChatResponse]:
    """与 AI 助手对话，支持多轮会话。"""
    service = AIService(db)
    result = await service.chat(req)
    return ApiResponse.ok(data=result)


@router.post(
    "/recommend",
    summary="AI 智能推荐餐厅",
    response_model=ApiResponse[RecommendResponse],
)
async def ai_recommend(
    req: RecommendRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RecommendResponse]:
    """根据口味、预算、位置等条件智能推荐餐厅。"""
    service = AIService(db)
    result = await service.recommend(req)
    return ApiResponse.ok(data=result)


@router.post(
    "/review-summary",
    summary="AI 总结店铺评论",
    response_model=ApiResponse[ReviewSummaryResponse],
)
async def ai_review_summary(
    req: ReviewSummaryRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ReviewSummaryResponse]:
    """AI 自动提炼店铺的好评/差评关键词，生成整体评价总结。"""
    service = AIService(db)
    result = await service.summarize_reviews(req)
    return ApiResponse.ok(data=result)


@router.post(
    "/generate-review",
    summary="AI 帮写点评",
    response_model=ApiResponse[GenerateReviewResponse],
)
async def ai_generate_review(
    req: GenerateReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[GenerateReviewResponse]:
    """输入评分和关键词，AI 自动生成完整点评文案。"""
    service = AIService(db)
    result = await service.generate_review(req)
    return ApiResponse.ok(data=result)
