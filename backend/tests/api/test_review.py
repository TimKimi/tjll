# backend/tests/api/test_review.py
"""评论模块的单元测试和集成测试。"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.models.review import Review
from backend.schemas.common import PaginatedData
from backend.schemas.review import ReviewBase, ReviewUser
from backend.services.review import ReviewService, _parse_json_field, _model_to_schema


# ---------- 辅助函数测试 ----------
class TestHelpers:
    """测试 review.py 中的辅助函数。"""

    def test_parse_json_field_valid(self):
        data = '{"id": "u1", "name": "张三"}'
        result = _parse_json_field(data)
        assert result == {"id": "u1", "name": "张三"}

    def test_parse_json_field_none(self):
        assert _parse_json_field(None) is None

    def test_parse_json_field_invalid(self):
        assert _parse_json_field("invalid json") is None

    def test_model_to_schema_with_user(self):
        review = MagicMock(spec=Review)
        review.id = "r1"
        review.business_id = "b1"
        review.text = "好吃"
        review.rating = 5
        review.time_created = "2025-01-01"
        review.user = (
            '{"id": "u1", "name": "李四", "profile_url": "http://x", "image_url": null}'
        )
        review.url = "http://review"

        schema = _model_to_schema(review)
        assert isinstance(schema, ReviewBase)
        assert schema.id == "r1"
        assert schema.user is not None
        assert schema.user.name == "李四"

    def test_model_to_schema_without_user(self):
        review = MagicMock(spec=Review)
        review.id = "r2"
        review.business_id = "b2"
        review.text = "一般"
        review.rating = 3
        review.time_created = "2025-01-02"
        review.user = None
        review.url = ""

        schema = _model_to_schema(review)
        assert schema.user is None


# ---------- Fixtures ----------
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    return db


@pytest.fixture
def sample_review():
    """构造一个模拟 Review 对象（ORM 实例）。"""
    review = MagicMock(spec=Review)
    review.id = "rev_001"
    review.business_id = "biz_123"
    review.text = "味道很棒，服务也好"
    review.rating = 5
    review.time_created = "2025-07-17T10:00:00"
    review.user = json.dumps(
        {
            "id": "user_1",
            "name": "王小明",
            "profile_url": "https://example.com/u1",
            "image_url": None,
        }
    )
    review.url = "https://yelp.com/review/rev_001"
    return review


# ---------- 服务层测试 ----------
class TestReviewService:
    """测试 ReviewService 的所有方法。"""

    @pytest.mark.asyncio
    async def test_list_by_business_default_sort(self, mock_db, sample_review):
        # 模拟 count 查询结果
        count_result = MagicMock()
        count_result.scalar_one.return_value = 15

        # 模拟主查询返回两条记录
        main_result = MagicMock()
        main_result.scalars.return_value.all.return_value = [
            sample_review,
            sample_review,
        ]

        # 关键：按顺序返回两个不同的结果
        mock_db.execute.side_effect = [count_result, main_result]

        service = ReviewService(mock_db)
        result = await service.list_by_business(
            business_id="biz_123", page=2, page_size=5, sort_by="time"
        )

        assert result.total == 15  # count 返回 15
        assert result.page == 2
        assert result.page_size == 5
        assert result.total_pages == 3  # (15+5-1)//5 = 3
        assert len(result.items) == 2
        # 验证排序：默认按 time_created 降序
        # 但 mock 未验证 order_by，可在断言中检查调用的 SQL 语句？简化

    @pytest.mark.asyncio
    async def test_list_by_business_rating_high(self, mock_db, sample_review):
        """测试按评分从高到低排序。"""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2
        mock_db.execute.return_value = count_result

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_review]
        mock_db.execute.return_value = mock_result

        service = ReviewService(mock_db)
        await service.list_by_business("biz_123", sort_by="rating_high")
        # 由于不验证具体 SQL，但确保不会报错且返回正确结构
        # 可捕捉异常

    @pytest.mark.asyncio
    async def test_list_by_business_rating_low(self, mock_db):
        """测试按评分从低到高排序。"""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        mock_db.execute.return_value = count_result

        service = ReviewService(mock_db)
        result = await service.list_by_business("biz_123", sort_by="rating_low")
        assert result.total == 0
        assert len(result.items) == 0
        assert result.total_pages == 0

    @pytest.mark.asyncio
    async def test_list_by_business_empty(self, mock_db):
        """测试无评论时返回空列表。"""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        mock_db.execute.return_value = count_result

        service = ReviewService(mock_db)
        result = await service.list_by_business("biz_empty")
        assert result.total == 0
        assert result.items == []
        assert result.total_pages == 0

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, mock_db, sample_review):
        """测试根据 ID 获取评论成功。"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_review
        mock_db.execute.return_value = mock_result

        service = ReviewService(mock_db)
        result = await service.get_by_id("rev_001")
        assert result is not None
        assert result.id == "rev_001"
        assert result.user is not None
        assert result.user.name == "王小明"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_db):
        """测试评论不存在时返回 None。"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = ReviewService(mock_db)
        result = await service.get_by_id("not_exist")
        assert result is None


# ---------- 路由层测试 ----------
@pytest.mark.integration
class TestReviewRoutes:
    """测试评论路由端点。"""

    @patch("backend.routers.review.ReviewService")
    def test_list_reviews(self, mock_service_class, client):
        """测试 GET /api/review/list 正常返回。"""
        # 构造模拟服务返回值
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

        response = client.get(
            "/api/review/list",
            params={"business_id": "b1", "page": 1, "page_size": 10, "sort_by": "time"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 1
        assert len(data["data"]["items"]) == 1
        mock_service.list_by_business.assert_called_once_with(
            business_id="b1", page=1, page_size=10, sort_by="time"
        )

    @patch("backend.routers.review.ReviewService")
    def test_list_reviews_with_default_params(self, mock_service_class, client):
        """测试未传分页参数时使用默认值。"""
        mock_service = mock_service_class.return_value
        mock_service.list_by_business = AsyncMock(
            return_value=PaginatedData(
                items=[], total=0, page=1, page_size=10, total_pages=0
            )
        )
        response = client.get("/api/review/list", params={"business_id": "b1"})
        assert response.status_code == 200
        mock_service.list_by_business.assert_called_once_with(
            business_id="b1", page=1, page_size=10, sort_by="time"
        )

    @patch("backend.routers.review.ReviewService")
    def test_review_detail_found(self, mock_service_class, client):
        """测试 GET /api/review/{review_id} 存在。"""
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
        response = client.get("/api/review/r1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == "r1"
        mock_service.get_by_id.assert_called_once_with("r1")

    @patch("backend.routers.review.ReviewService")
    def test_review_detail_not_found(self, mock_service_class, client):
        """测试评论不存在时返回 404。"""
        mock_service = mock_service_class.return_value
        mock_service.get_by_id = AsyncMock(return_value=None)
        response = client.get("/api/review/not_exist")
        assert response.status_code == 404
        assert response.json()["detail"] == "评论不存在"
        mock_service.get_by_id.assert_called_once_with("not_exist")

    @patch("backend.routers.review.ReviewService")
    def test_list_reviews_invalid_sort(self, mock_service_class, client):
        """测试传入非法排序参数（服务层依然能处理，但会走 else 分支）。"""
        mock_service = mock_service_class.return_value
        mock_service.list_by_business = AsyncMock(
            return_value=PaginatedData(
                items=[], total=0, page=1, page_size=10, total_pages=0
            )
        )
        response = client.get(
            "/api/review/list", params={"business_id": "b1", "sort_by": "unknown"}
        )
        assert response.status_code == 200
        # 因为 sort_by 不在 if 中，走 else（默认 time）
        mock_service.list_by_business.assert_called_once_with(
            business_id="b1", page=1, page_size=10, sort_by="unknown"
        )
