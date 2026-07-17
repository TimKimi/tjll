"""AI 助手业务逻辑层。

当前为基础版本，返回模拟数据；后续可接入 DeepSeek / OpenAI 等 LLM 实现真实 AI 能力。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.business import Business
from backend.schemas.ai import (
    ChatRequest,
    ChatResponse,
    GenerateReviewRequest,
    GenerateReviewResponse,
    RecommendItem,
    RecommendRequest,
    RecommendResponse,
    ReviewSummaryRequest,
    ReviewSummaryResponse,
)


class AIService:
    """AI 助手服务。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_config = settings.llm_kwargs

    async def chat(self, req: ChatRequest) -> ChatResponse:
        """AI 对话。

        当前为 Mock 实现，返回固定回复。
        后续可接入 LLM：调用 OpenAI 兼容接口，结合 RAG 检索店铺知识。
        """
        conversation_id = req.conversation_id or str(uuid.uuid4())

        # Mock 回复
        if "推荐" in req.message or "好吃" in req.message:
            reply = (
                "根据你的需求，我为你推荐几家不错的餐厅：\n"
                "1. 川味轩 - 正宗川菜，麻辣鲜香，人均约80元\n"
                "2. 粤味小馆 - 精致粤菜，适合聚餐，人均约120元\n"
                "3. 和风日料 - 新鲜刺身，环境优雅，人均约200元\n\n"
                "你可以告诉我具体的口味偏好或预算，我帮你精准推荐！"
            )
        elif "评论" in req.message or "评价" in req.message:
            reply = "我可以帮你总结店铺评论、生成点评文案，或者解答关于某家店的问题。请告诉我店铺名称。"
        else:
            reply = (
                f"你好！我是探店AI助手，可以帮你：\n"
                f"• 智能推荐餐厅（告诉我口味、预算、位置）\n"
                f"• 总结店铺评论（快速了解口碑）\n"
                f"• 帮写点评文案（输入关键词即可生成）\n"
                f"• 解答美食相关问题\n\n"
                f"你刚才说的是：「{req.message}」，有什么我能帮你的吗？"
            )

        return ChatResponse(reply=reply, conversation_id=conversation_id)

    async def recommend(self, req: RecommendRequest) -> RecommendResponse:
        """AI 智能推荐餐厅。

        当前从数据库取评分最高的几家作为 Mock 推荐。
        """
        stmt = select(Business).order_by(Business.rating.desc()).limit(3)
        result = await self.db.execute(stmt)
        businesses = result.scalars().all()

        recommendations: list[RecommendItem] = []
        for i, biz in enumerate(businesses):
            reasons = [
                "评分高，口碑好，是当地的人气之选",
                "菜品丰富，口味正宗，值得一试",
                "环境优雅，服务周到，适合各种场合",
            ]
            recommendations.append(
                RecommendItem(
                    business_id=biz.id,
                    name=biz.name,
                    reason=reasons[i % len(reasons)],
                )
            )

        location_desc = req.location or "当前地区"
        summary = f"为你在{location_desc}精选了 {len(recommendations)} 家优质餐厅，综合评分与口碑都很不错。"

        return RecommendResponse(recommendations=recommendations, summary=summary)

    async def summarize_reviews(
        self, req: ReviewSummaryRequest
    ) -> ReviewSummaryResponse:
        """AI 总结店铺评论。

        当前为 Mock 实现，后续可结合 RAG 真实总结。
        """
        stmt = select(Business).where(Business.id == req.business_id)
        result = await self.db.execute(stmt)
        biz = result.scalar_one_or_none()

        business_name = biz.name if biz else "未知店铺"

        return ReviewSummaryResponse(
            business_id=req.business_id,
            business_name=business_name,
            pros=[
                "味道正宗，菜品丰富",
                "服务态度好，上菜快",
                "环境干净整洁",
                "性价比高，分量足",
            ],
            cons=[
                "高峰期需要排队",
                "停车位较少",
                "部分菜品偏咸",
            ],
            summary=(
                f"{business_name}整体评价较好，主打地道口味，服务和环境都受到好评。"
                f"主要槽点集中在高峰时段排队和停车问题，建议错峰前往。"
            ),
        )

    async def generate_review(
        self, req: GenerateReviewRequest
    ) -> GenerateReviewResponse:
        """AI 生成点评文案。

        当前为模板生成，后续可接入 LLM 实现更自然的文案。
        """
        rating_text = (
            "非常棒" if req.rating >= 4 else "还不错" if req.rating >= 3 else "一般"
        )
        keywords = "、".join(req.keywords) if req.keywords else "整体体验"

        content = (
            f"⭐ {req.rating}星 {rating_text}！\n\n"
            f"{keywords}都很满意。店里环境很好，服务也很热情。"
            f"菜品口味正宗，分量也足，性价比挺高的。\n\n"
            f"总的来说是一次不错的体验，有机会还会再来，推荐给大家！"
        )

        return GenerateReviewResponse(content=content)
