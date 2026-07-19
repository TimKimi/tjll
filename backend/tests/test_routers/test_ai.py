"""AI 助手路由集成测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from backend.schemas.ai import (
    ChatResponse,
    GenerateReviewResponse,
    RecommendItem,
    RecommendResponse,
    ReviewSummaryResponse,
)


class TestAIRoutes:
    """路由层测试 - patch 服务类本身"""

    @patch("backend.routers.ai.AIService")
    def test_chat(self, mock_service_class, client):
        mock_instance = mock_service_class.return_value
        mock_instance.chat = AsyncMock(
            return_value=ChatResponse(reply="测试回复", conversation_id="conv_123")
        )
        response = client.post(
            "/api/ai/chat",
            json={"message": "推荐餐厅", "conversation_id": None, "stream": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["reply"] == "测试回复"
        mock_instance.chat.assert_called_once()

    @patch("backend.routers.ai.AIService")
    def test_recommend(self, mock_service_class, client):
        mock_instance = mock_service_class.return_value
        mock_instance.recommend = AsyncMock(
            return_value=RecommendResponse(
                recommendations=[
                    RecommendItem(business_id="b1", name="店1", reason="好吃")
                ],
                summary="总结",
            )
        )
        response = client.post(
            "/api/ai/recommend",
            json={"location": "成都", "cuisine": "川菜", "budget": "中等"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["summary"] == "总结"
        mock_instance.recommend.assert_called_once()

    @patch("backend.routers.ai.AIService")
    def test_review_summary(self, mock_service_class, client):
        mock_instance = mock_service_class.return_value
        mock_instance.summarize_reviews = AsyncMock(
            return_value=ReviewSummaryResponse(
                business_id="b1",
                business_name="测试店",
                pros=["味道好"],
                cons=["排队"],
                summary="整体不错",
            )
        )
        response = client.post("/api/ai/review-summary", json={"business_id": "b1"})
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["business_name"] == "测试店"
        mock_instance.summarize_reviews.assert_called_once()

    @patch("backend.routers.ai.AIService")
    def test_generate_review(self, mock_service_class, client):
        mock_instance = mock_service_class.return_value
        mock_instance.generate_review = AsyncMock(
            return_value=GenerateReviewResponse(content="生成的点评内容")
        )
        response = client.post(
            "/api/ai/generate-review",
            json={
                "business_id": "b1",
                "rating": 5,
                "keywords": ["好吃"],
                "style": "normal",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["content"] == "生成的点评内容"
        mock_instance.generate_review.assert_called_once()
