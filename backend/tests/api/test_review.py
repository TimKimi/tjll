# backend/tests/api/test_review.py
"""评论模块的单元测试和集成测试。"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.models.review import Review
from backend.schemas.common import PaginatedData
from backend.schemas.review import ReviewBase, ReviewUser
from backend.services.review import ReviewService, _parse_json_field, _model_to_schema
from backend.services.yelp import YelpError


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


@pytest.fixture
def mock_yelp_review():
    """模拟 Yelp API 返回的评论对象（YelpReview 结构）"""
    yelp_review = MagicMock()
    yelp_review.id = "yelp_rev_001"
    yelp_review.text = "Great food!"
    yelp_review.rating = 5
    yelp_review.time_created = "2025-07-17T10:00:00"
    yelp_review.url = "https://yelp.com/review/001"
    yelp_review.user = MagicMock()
    yelp_review.user.id = "yelp_user_1"
    yelp_review.user.name = "John Doe"
    yelp_review.user.profile_url = "https://yelp.com/user/1"
    yelp_review.user.image_url = "https://yelp.com/img.jpg"
    return yelp_review


# ---------- 服务层测试 ----------
class TestReviewService:
    """测试 ReviewService 的所有方法。"""

    @pytest.mark.asyncio
    async def test_list_by_business_default_source_db(self, mock_db, sample_review):
        """测试默认 source='db' 时走数据库查询"""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 15
        main_result = MagicMock()
        main_result.scalars.return_value.all.return_value = [
            sample_review,
            sample_review,
        ]
        mock_db.execute.side_effect = [count_result, main_result]

        service = ReviewService(mock_db)
        result = await service.list_by_business(
            business_id="biz_123", page=2, page_size=5, sort_by="time"
        )  # source 默认 db

        assert result.total == 15
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_list_by_business_source_yelp_success(
        self, mock_db, mock_yelp_review
    ):
        """测试 source='yelp' 时调用 Yelp API 成功"""
        # 模拟 YelpService.get_reviews 返回
        mock_yelp_response = MagicMock()
        mock_yelp_response.reviews = [mock_yelp_review]
        mock_yelp_response.total = 1  # 可选

        with patch("backend.services.review.YelpService") as MockYelpService:
            mock_yelp_instance = MockYelpService.return_value
            mock_yelp_instance.get_reviews = AsyncMock(return_value=mock_yelp_response)

            service = ReviewService(mock_db)  # 此时 _yelp 是 mock 实例
            result = await service.list_by_business(
                business_id="biz_123",
                page=1,
                page_size=10,
                sort_by="time",
                source="yelp",
            )

            # 验证调用
            mock_yelp_instance.get_reviews.assert_called_once_with(
                business_id="biz_123", limit=10, offset=0
            )
            # 验证返回结果
            assert result.total == 1
            assert len(result.items) == 1
            assert result.items[0].id == "yelp_rev_001"
            assert result.items[0].text == "Great food!"
            assert result.items[0].user is not None
            assert result.items[0].user.name == "John Doe"

    @pytest.mark.asyncio
    async def test_list_by_business_source_yelp_yelp_error(self, mock_db):
        """测试 Yelp API 抛出 YelpError 时转为 HTTPException"""
        with patch("backend.services.review.YelpService") as MockYelpService:
            mock_yelp_instance = MockYelpService.return_value
            mock_yelp_instance.get_reviews = AsyncMock(
                side_effect=YelpError(
                    status_code=404, code="NOT_FOUND", description="商家不存在"
                )
            )

            service = ReviewService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.list_by_business(business_id="not_exist", source="yelp")
            assert exc_info.value.status_code == 404
            assert "商家不存在" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_by_business_rating_high(self, mock_db, sample_review):
        """测试按评分从高到低排序（数据库）"""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2
        mock_db.execute.return_value = count_result

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_review]
        mock_db.execute.return_value = mock_result

        service = ReviewService(mock_db)
        await service.list_by_business("biz_123", sort_by="rating_high", source="db")
        # 确保未调用 yelp
        # 由于 service._yelp 是真实对象，但未 mock，实际不会调用，但我们可以通过断言 call_count 等

    @pytest.mark.asyncio
    async def test_list_by_business_rating_low(self, mock_db):
        """测试按评分从低到高排序"""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        mock_db.execute.return_value = count_result

        service = ReviewService(mock_db)
        result = await service.list_by_business(
            "biz_123", sort_by="rating_low", source="db"
        )
        assert result.total == 0
        assert len(result.items) == 0
        assert result.total_pages == 0

    @pytest.mark.asyncio
    async def test_list_by_business_empty(self, mock_db):
        """测试无评论时返回空列表"""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        mock_db.execute.return_value = count_result

        service = ReviewService(mock_db)
        result = await service.list_by_business("biz_empty", source="db")
        assert result.total == 0
        assert result.items == []
        assert result.total_pages == 0

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, mock_db, sample_review):
        """测试根据 ID 获取评论成功"""
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
        """测试评论不存在时返回 None"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = ReviewService(mock_db)
        result = await service.get_by_id("not_exist")
        assert result is None


# ---------- 路由层测试 ----------
class TestReviewRoutes:
    """测试评论路由端点。"""

    @patch("backend.routers.review.ReviewService")
    def test_list_reviews(self, mock_service_class, client):
        """测试 POST /api/review/list 正常返回"""
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
        assert len(data["data"]["items"]) == 1
        mock_service.list_by_business.assert_called_once_with(
            business_id="b1", page=1, page_size=10, sort_by="time", source="db"
        )

    @patch("backend.routers.review.ReviewService")
    def test_list_reviews_with_default_params(self, mock_service_class, client):
        """测试未传分页参数时使用默认值"""
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
        """测试显式指定 source='yelp'"""
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
        """测试 POST /api/review/{review_id} 存在"""
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
        """测试评论不存在时返回 404"""
        mock_service = mock_service_class.return_value
        mock_service.get_by_id = AsyncMock(return_value=None)
        response = client.post("/api/review/not_exist")
        assert response.status_code == 404
        assert response.json()["detail"] == "评论不存在"
        mock_service.get_by_id.assert_called_once_with("not_exist")

    @patch("backend.routers.review.ReviewService")
    def test_list_reviews_invalid_sort(self, mock_service_class, client):
        """测试传入非法排序参数（走默认 time）"""
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
