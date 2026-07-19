"""AI 助手服务层单元测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.models.business import Business
from backend.schemas.ai import (
    ChatRequest,
    GenerateReviewRequest,
    RecommendRequest,
    ReviewSummaryRequest,
)
from backend.services.ai import AIService


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def sample_business():
    return Business(id="biz_001", name="川味轩", rating=4.5, address="成都锦江区")


class TestAIService:
    """业务逻辑层测试"""

    @pytest.mark.asyncio
    async def test_chat_with_recommend_keyword(self, mock_db):
        service = AIService(mock_db)
        req = ChatRequest(message="推荐一下好吃的")
        resp = await service.chat(req)
        assert "推荐几家不错的餐厅" in resp.reply

    @pytest.mark.asyncio
    async def test_chat_with_review_keyword(self, mock_db):
        service = AIService(mock_db)
        req = ChatRequest(message="帮我总结评论", conversation_id="existing")
        resp = await service.chat(req)
        assert "总结店铺评论" in resp.reply
        assert resp.conversation_id == "existing"

    @pytest.mark.asyncio
    async def test_chat_other(self, mock_db):
        service = AIService(mock_db)
        req = ChatRequest(message="今天天气不错")
        resp = await service.chat(req)
        assert "我是探店AI助手" in resp.reply

    @pytest.mark.asyncio
    async def test_recommend_with_data(self, mock_db, sample_business):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_business]
        mock_db.execute.return_value = mock_result

        service = AIService(mock_db)
        req = RecommendRequest(location="成都", cuisine="川菜")
        resp = await service.recommend(req)
        assert len(resp.recommendations) == 1
        assert resp.recommendations[0].business_id == "biz_001"
        assert "精选了 1 家" in resp.summary

    @pytest.mark.asyncio
    async def test_recommend_empty(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = AIService(mock_db)
        req = RecommendRequest(location="未知")
        resp = await service.recommend(req)
        assert len(resp.recommendations) == 0
        assert "精选了 0 家" in resp.summary

    @pytest.mark.asyncio
    async def test_summarize_reviews_with_business(self, mock_db, sample_business):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_business
        mock_db.execute.return_value = mock_result

        service = AIService(mock_db)
        req = ReviewSummaryRequest(business_id="biz_001")
        resp = await service.summarize_reviews(req)
        assert resp.business_name == "川味轩"
        assert "川味轩整体评价较好" in resp.summary

    @pytest.mark.asyncio
    async def test_summarize_reviews_without_business(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AIService(mock_db)
        req = ReviewSummaryRequest(business_id="not_exist")
        resp = await service.summarize_reviews(req)
        assert resp.business_name == "未知店铺"

    @pytest.mark.asyncio
    async def test_generate_review_high_rating(self, mock_db):
        service = AIService(mock_db)
        req = GenerateReviewRequest(
            business_id="b1", rating=5, keywords=["味道", "服务"]
        )
        resp = await service.generate_review(req)
        assert "⭐ 5星 非常棒！" in resp.content
        assert "味道、服务都很满意" in resp.content

    @pytest.mark.asyncio
    async def test_generate_review_mid_rating(self, mock_db):
        service = AIService(mock_db)
        req = GenerateReviewRequest(business_id="b1", rating=3, keywords=[])
        resp = await service.generate_review(req)
        assert "⭐ 3星 还不错！" in resp.content

    @pytest.mark.asyncio
    async def test_generate_review_low_rating(self, mock_db):
        service = AIService(mock_db)
        req = GenerateReviewRequest(business_id="b1", rating=1, keywords=["环境"])
        resp = await service.generate_review(req)
        assert "⭐ 1星 一般" in resp.content
        assert "环境" in resp.content
