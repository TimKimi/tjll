"""店铺路由集成测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.business import (
    BusinessDetail,
    BusinessListQuery,
    Category,
    Location,
)
from backend.schemas.common import PaginatedData


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestBusinessRoutes:
    """测试店铺路由端点。"""

    @patch("backend.routers.business.BusinessService")
    def test_list_businesses(self, mock_service_class, client):
        mock_service = mock_service_class.return_value
        mock_service.list_businesses = AsyncMock(
            return_value=PaginatedData(
                items=[
                    BusinessDetail(
                        id="b1",
                        name="餐厅1",
                        rating=4.0,
                        review_count=10,
                        categories=[Category(alias="c1", title="C1")],
                        location=Location(city="成都"),
                    )
                ],
                total=1,
                page=1,
                page_size=10,
                total_pages=1,
            )
        )

        response = client.get(
            "/api/business/list",
            params={
                "keyword": "餐厅",
                "category": "chinese",
                "location": "成都",
                "sort_by": "rating",
                "page": 1,
                "page_size": 10,
                "source": "db",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 1
        assert len(data["data"]["items"]) == 1
        call_args = mock_service.list_businesses.call_args[0][0]
        assert isinstance(call_args, BusinessListQuery)
        assert call_args.keyword == "餐厅"
        assert call_args.category == "chinese"
        assert call_args.source == "db"

    @patch("backend.routers.business.BusinessService")
    def test_list_businesses_defaults(self, mock_service_class, client):
        mock_service = mock_service_class.return_value
        mock_service.list_businesses = AsyncMock(
            return_value=PaginatedData(
                items=[], total=0, page=1, page_size=10, total_pages=0
            )
        )
        response = client.get("/api/business/list")
        assert response.status_code == 200
        call_args = mock_service.list_businesses.call_args[0][0]
        assert call_args.page == 1
        assert call_args.page_size == 10
        assert call_args.sort_by == "rating"
        assert call_args.keyword is None
        assert call_args.source == "db"

    @patch("backend.routers.business.BusinessService")
    def test_list_businesses_with_yelp_source(self, mock_service_class, client):
        mock_service = mock_service_class.return_value
        mock_service.list_businesses = AsyncMock(
            return_value=PaginatedData(
                items=[], total=0, page=1, page_size=10, total_pages=0
            )
        )
        response = client.get(
            "/api/business/list",
            params={
                "keyword": "pizza",
                "location": "New York",
                "source": "yelp",
                "page": 2,
                "page_size": 5,
                "sort_by": "review_count",
            },
        )
        assert response.status_code == 200
        call_args = mock_service.list_businesses.call_args[0][0]
        assert call_args.source == "yelp"
        assert call_args.keyword == "pizza"
        assert call_args.location == "New York"

    @patch("backend.routers.business.BusinessService")
    def test_business_detail_found(self, mock_service_class, client):
        mock_service = mock_service_class.return_value
        mock_service.get_by_id = AsyncMock(
            return_value=BusinessDetail(
                id="b1",
                name="测试店",
                rating=4.5,
                review_count=5,
            )
        )
        response = client.get("/api/business/b1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == "b1"
        mock_service.get_by_id.assert_called_once_with("b1")

    @patch("backend.routers.business.BusinessService")
    def test_business_detail_not_found(self, mock_service_class, client):
        mock_service = mock_service_class.return_value
        mock_service.get_by_id = AsyncMock(return_value=None)
        response = client.get("/api/business/not_exist")
        assert response.status_code == 404
        assert response.json()["detail"] == "店铺不存在"
        mock_service.get_by_id.assert_called_once_with("not_exist")
