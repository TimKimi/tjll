"""评论路由集成测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.common import PaginatedData
from backend.schemas.review import ReviewBase, ReviewUser


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestReviewRoutes:
    """测试评论路由端点。"""

    @patch("backend.routers.review.ReviewService")
    def test_list_reviews(self, mock_service_class, client):
        mock_service = mock_service_class.return_value
        mock_service.list_by_business = AsyncMock(
            return_value=PaginatedData(
                items=[
                    ReviewBase(
                        id="r1",
                        business_id="b1",
                        text="好",
                        rating=5,
                        time_created="2025-01-01",
                        user=ReviewUser(id="u1", name="A"),
                        url="",
                    )
                ],
                total=1,
                page=1,
                page_size=10,
                total_pages=1,
            )
        )
        response = client.post(
            "/api/review/list",
            params={
                "business_id": "b1",
                "page": 1,
                "page_size": 10,
                "sort_by": "time",
                "source": "db",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 1
        mock_service.list_by_business.assert_called_once_with(
            business_id="b1", page=1, page_size=10, sort_by="time", source="db"
        )

    @patch("backend.routers.review.ReviewService")
    def test_list_reviews_with_default_params(self, mock_service_class, client):
        mock_service = mock_service_class.return_value
        mock_service.list_by_business = AsyncMock(
            return_value=PaginatedData(
                items=[], total=0, page=1, page_size=10, total_pages=0
            )
        )
        response = client.post("/api/review/list", params={"business_id": "b1"})
        assert response.status_code == 200
        mock_service.list_by_business.assert_called_once_with(
            business_id="b1", page=1, page_size=10, sort_by="time", source="db"
        )

    @patch("backend.routers.review.ReviewService")
    def test_list_reviews_with_yelp_source(self, mock_service_class, client):
        mock_service = mock_service_class.return_value
        mock_service.list_by_business = AsyncMock(
            return_value=PaginatedData(
                items=[], total=0, page=1, page_size=10, total_pages=0
            )
        )
        response = client.post(
            "/api/review/list",
            params={"business_id": "b1", "source": "yelp", "page": 1, "page_size": 5},
        )
        assert response.status_code == 200
        mock_service.list_by_business.assert_called_once_with(
            business_id="b1", page=1, page_size=5, sort_by="time", source="yelp"
        )

    @patch("backend.routers.review.ReviewService")
    def test_review_detail_found(self, mock_service_class, client):
        mock_service = mock_service_class.return_value
        mock_service.get_by_id = AsyncMock(
            return_value=ReviewBase(
                id="r1",
                business_id="b1",
                text="好",
                rating=5,
                time_created="2025-01-01",
                user=None,
                url="",
            )
        )
        response = client.post("/api/review/r1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == "r1"
        mock_service.get_by_id.assert_called_once_with("r1")

    @patch("backend.routers.review.ReviewService")
    def test_review_detail_not_found(self, mock_service_class, client):
        mock_service = mock_service_class.return_value
        mock_service.get_by_id = AsyncMock(return_value=None)
        response = client.post("/api/review/not_exist")
        assert response.status_code == 404
        assert response.json()["detail"] == "评论不存在"
        mock_service.get_by_id.assert_called_once_with("not_exist")

    @patch("backend.routers.review.ReviewService")
    def test_list_reviews_invalid_sort(self, mock_service_class, client):
        mock_service = mock_service_class.return_value
        mock_service.list_by_business = AsyncMock(
            return_value=PaginatedData(
                items=[], total=0, page=1, page_size=10, total_pages=0
            )
        )
        response = client.post(
            "/api/review/list",
            params={"business_id": "b1", "sort_by": "unknown", "source": "db"},
        )
        assert response.status_code == 200
        mock_service.list_by_business.assert_called_once_with(
            business_id="b1", page=1, page_size=10, sort_by="unknown", source="db"
        )
