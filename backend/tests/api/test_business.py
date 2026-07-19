# backend/tests/api/test_business.py
"""店铺模块的单元测试和集成测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.models.business import Business
from backend.schemas.business import (
    BusinessDetail,
    BusinessListQuery,
    Category,
    Location,
)
from backend.schemas.common import PaginatedData
from backend.services.business import (
    BusinessService,
    _parse_json_field,
    _parse_json_list,
    _model_to_schema,
)


# ---------- 辅助函数测试 ----------
class TestHelpers:
    """测试 business.py 中的辅助函数。"""

    def test_parse_json_field_valid(self):
        data = '{"key": "value"}'
        assert _parse_json_field(data) == {"key": "value"}

    def test_parse_json_field_none(self):
        assert _parse_json_field(None) is None

    def test_parse_json_field_invalid(self):
        assert _parse_json_field("not json") is None

    def test_parse_json_list_valid(self):
        data = '["a", "b", "c"]'
        assert _parse_json_list(data) == ["a", "b", "c"]

    def test_parse_json_list_none(self):
        assert _parse_json_list(None) == []

    def test_parse_json_list_invalid(self):
        assert _parse_json_list("{invalid}") == []

    def test_parse_json_list_not_list(self):
        assert _parse_json_list('{"a":1}') == []

    def test_model_to_schema_full(self):
        """测试 _model_to_schema 完整转换。"""
        biz = MagicMock(spec=Business)
        biz.id = "b1"
        biz.alias = "alias1"
        biz.name = "Test Restaurant"
        biz.image_url = "http://img"
        biz.is_closed = False
        biz.url = "http://url"
        biz.review_count = 100
        biz.rating = 4.5
        biz.price = "$$"
        biz.categories = '[{"alias": "italian", "title": "Italian"}]'
        biz.address = '{"address1": "123 Main", "city": "NYC"}'
        biz.latitude = 40.7128
        biz.longitude = -74.0060
        biz.phone = "123456"
        biz.display_phone = "+1 123-456"
        biz.transactions = '["delivery", "pickup"]'
        biz.photos = '["photo1", "photo2"]'
        biz.hours = '{"monday": "10-20"}'

        schema = _model_to_schema(biz)
        assert isinstance(schema, BusinessDetail)
        assert schema.id == "b1"
        assert schema.alias == "alias1"
        assert schema.name == "Test Restaurant"
        assert schema.categories == [Category(alias="italian", title="Italian")]
        assert schema.location is not None
        assert schema.location.city == "NYC"
        assert schema.coordinates is not None
        assert schema.coordinates.latitude == 40.7128
        assert schema.transactions == ["delivery", "pickup"]
        assert schema.photos == ["photo1", "photo2"]
        assert schema.hours == {"monday": "10-20"}

    def test_model_to_schema_missing_coords(self):
        """测试无坐标时 coordinates 为 None，location 为空 Location 对象。"""
        biz = MagicMock(spec=Business)
        biz.id = "b2"
        biz.alias = ""
        biz.name = "No Coords"
        biz.image_url = None
        biz.is_closed = False
        biz.url = None
        biz.review_count = 0
        biz.rating = 0.0
        biz.price = None
        biz.categories = None
        biz.address = None
        biz.latitude = None
        biz.longitude = None
        biz.phone = ""
        biz.display_phone = ""
        biz.transactions = None
        biz.photos = None
        biz.hours = None

        schema = _model_to_schema(biz)
        assert schema.coordinates is None
        # 业务逻辑会返回一个空的 Location 对象（所有字段为 None 或默认空）
        assert schema.location is not None
        assert schema.location.address1 is None
        assert schema.location.city is None
        assert schema.location.state is None
        assert schema.location.zip_code is None
        assert schema.location.country is None
        assert schema.location.display_address == []
        assert schema.categories == []
        assert schema.transactions == []
        assert schema.photos == []
        assert schema.hours is None


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
def sample_business():
    """构造模拟 Business ORM 对象。"""
    biz = MagicMock(spec=Business)
    biz.id = "biz_001"
    biz.alias = "test_biz"
    biz.name = "测试餐厅"
    biz.image_url = "http://example.com/img.jpg"
    biz.is_closed = False
    biz.url = "http://example.com"
    biz.review_count = 42
    biz.rating = 4.2
    biz.price = "$$"
    biz.categories = '[{"alias": "chinese", "title": "Chinese"}]'
    biz.address = '{"address1": "1 Main St", "city": "成都", "country": "CN"}'
    biz.latitude = 30.5728
    biz.longitude = 104.0668
    biz.phone = "028-123456"
    biz.display_phone = "+86 28 123456"
    biz.transactions = '["delivery"]'
    biz.photos = '["photo_url"]'
    biz.hours = '{"mon": "10:00-22:00"}'
    return biz


# ---------- 服务层测试 ----------
class TestBusinessService:
    """测试 BusinessService 的所有方法。"""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, mock_db, sample_business):
        """测试根据 ID 获取店铺成功。"""
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = sample_business
        mock_db.execute.return_value = result_mock

        service = BusinessService(mock_db)
        result = await service.get_by_id("biz_001")
        assert result is not None
        assert result.id == "biz_001"
        assert result.name == "测试餐厅"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_db):
        """测试店铺不存在时返回 None。"""
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock

        service = BusinessService(mock_db)
        result = await service.get_by_id("not_exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_businesses_default_source_db(self, mock_db, sample_business):
        """测试默认 source='db' 时走数据库查询（未传 source）。"""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 5
        main_result = MagicMock()
        main_result.scalars.return_value.all.return_value = [sample_business]
        mock_db.execute.side_effect = [count_result, main_result]

        query = BusinessListQuery(
            keyword="餐厅",
            category="chinese",
            location="成都",
            price="$$",
            sort_by="rating",
            page=2,
            page_size=2,
        )
        service = BusinessService(mock_db)
        result = await service.list_businesses(query)

        assert result.total == 5
        assert result.page == 2
        assert result.page_size == 2
        assert result.total_pages == 3
        assert len(result.items) == 1
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_list_businesses_source_yelp_success(self, mock_db):
        """测试 source='yelp' 时调用 YelpSearchService 成功返回数据。"""
        # 模拟 YelpSearchService 的返回
        mock_yelp_result = PaginatedData(
            items=[
                BusinessDetail(
                    id="yelp_biz_1",
                    name="Yelp 餐厅",
                    rating=4.8,
                    review_count=100,
                    categories=[Category(alias="sushi", title="Sushi")],
                    location=Location(city="Tokyo"),
                )
            ],
            total=1,
            page=1,
            page_size=10,
            total_pages=1,
        )

        with patch("backend.services.business.YelpSearchService") as MockYelpSearch:
            mock_yelp_instance = MockYelpSearch.return_value
            mock_yelp_instance.search_as_schema = AsyncMock(
                return_value=mock_yelp_result
            )

            query = BusinessListQuery(
                keyword="sushi",
                location="Tokyo",
                source="yelp",
                page=1,
                page_size=10,
            )
            service = BusinessService(mock_db)
            result = await service.list_businesses(query)

            # 验证调用了 YelpSearchService
            mock_yelp_instance.search_as_schema.assert_called_once_with(
                keyword="sushi",
                category=None,
                location="Tokyo",
                latitude=None,
                longitude=None,
                sort_by="rating",
                price=None,
                limit=10,
                offset=0,
            )
            # 验证返回结果正确
            assert result.total == 1
            assert result.items[0].id == "yelp_biz_1"
            assert result.items[0].name == "Yelp 餐厅"

    @pytest.mark.asyncio
    async def test_list_businesses_source_yelp_error(self, mock_db):
        """测试 YelpSearchService 抛出异常时，服务层向上传递（由路由处理）。"""
        with patch("backend.services.business.YelpSearchService") as MockYelpSearch:
            mock_yelp_instance = MockYelpSearch.return_value
            mock_yelp_instance.search_as_schema = AsyncMock(
                side_effect=ValueError(
                    "使用 Yelp 搜索时必须提供 location 或 latitude+longitude"
                )
            )

            query = BusinessListQuery(
                keyword="sushi",
                source="yelp",
                page=1,
                page_size=10,
            )
            service = BusinessService(mock_db)
            with pytest.raises(ValueError) as exc_info:
                await service.list_businesses(query)
            assert "location" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_businesses_sort_review_count(self, mock_db, sample_business):
        """测试按 review_count 排序。"""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        main_result = MagicMock()
        main_result.scalars.return_value.all.return_value = [sample_business]
        mock_db.execute.side_effect = [count_result, main_result]

        query = BusinessListQuery(sort_by="review_count")
        service = BusinessService(mock_db)
        result = await service.list_businesses(query)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_businesses_sort_default(self, mock_db, sample_business):
        """测试默认排序（rating）当 sort_by 无效时。"""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        main_result = MagicMock()
        main_result.scalars.return_value.all.return_value = [sample_business]
        mock_db.execute.side_effect = [count_result, main_result]

        query = BusinessListQuery(sort_by="unknown")
        service = BusinessService(mock_db)
        result = await service.list_businesses(query)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_businesses_empty(self, mock_db):
        """测试无结果。"""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        main_result = MagicMock()
        main_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [count_result, main_result]

        query = BusinessListQuery(keyword="不存在的关键词")
        service = BusinessService(mock_db)
        result = await service.list_businesses(query)
        assert result.total == 0
        assert result.items == []
        assert result.total_pages == 0

    @pytest.mark.asyncio
    async def test_list_businesses_without_price(self, mock_db, sample_business):
        """测试不传 price 时，不添加价格筛选。"""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        main_result = MagicMock()
        main_result.scalars.return_value.all.return_value = [sample_business]
        mock_db.execute.side_effect = [count_result, main_result]

        query = BusinessListQuery(keyword="餐厅")  # 无 price
        service = BusinessService(mock_db)
        result = await service.list_businesses(query)
        assert result.total == 1


# ---------- 路由层测试 ----------
@pytest.mark.integration
class TestBusinessRoutes:
    """测试店铺路由端点。"""

    @patch("backend.routers.business.BusinessService")
    def test_list_businesses(self, mock_service_class, client):
        """测试 GET /api/business/list 正常返回，包含 source 参数。"""
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

        response = client.post(
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
        # 验证服务调用参数，现在应包含 source='db'
        call_args = mock_service.list_businesses.call_args[0][0]
        assert isinstance(call_args, BusinessListQuery)
        assert call_args.keyword == "餐厅"
        assert call_args.category == "chinese"
        assert call_args.sort_by == "rating"
        assert call_args.source == "db"

    @patch("backend.routers.business.BusinessService")
    def test_list_businesses_defaults(self, mock_service_class, client):
        """测试未传参数时使用默认值，source 应为 db。"""
        mock_service = mock_service_class.return_value
        mock_service.list_businesses = AsyncMock(
            return_value=PaginatedData(
                items=[], total=0, page=1, page_size=10, total_pages=0
            )
        )
        response = client.post("/api/business/list")
        assert response.status_code == 200
        call_args = mock_service.list_businesses.call_args[0][0]
        assert call_args.page == 1
        assert call_args.page_size == 10
        assert call_args.sort_by == "rating"
        assert call_args.keyword is None
        assert call_args.source == "db"  # 默认 db

    @patch("backend.routers.business.BusinessService")
    def test_list_businesses_with_yelp_source(self, mock_service_class, client):
        """测试显式指定 source='yelp' 时，路由正确传递参数。"""
        mock_service = mock_service_class.return_value
        mock_service.list_businesses = AsyncMock(
            return_value=PaginatedData(
                items=[], total=0, page=1, page_size=10, total_pages=0
            )
        )
        response = client.post(
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
        assert call_args.page == 2
        assert call_args.page_size == 5
        assert call_args.sort_by == "review_count"

    @patch("backend.routers.business.BusinessService")
    def test_business_detail_found(self, mock_service_class, client):
        """测试 GET /api/business/{id} 存在。"""
        mock_service = mock_service_class.return_value
        mock_service.get_by_id = AsyncMock(
            return_value=BusinessDetail(
                id="b1",
                name="测试店",
                rating=4.5,
                review_count=5,
            )
        )
        response = client.post("/api/business/b1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == "b1"
        mock_service.get_by_id.assert_called_once_with("b1")

    @patch("backend.routers.business.BusinessService")
    def test_business_detail_not_found(self, mock_service_class, client):
        """测试店铺不存在返回 404。"""
        mock_service = mock_service_class.return_value
        mock_service.get_by_id = AsyncMock(return_value=None)
        response = client.post("/api/business/not_exist")
        assert response.status_code == 404
        assert response.json()["detail"] == "店铺不存在"
        mock_service.get_by_id.assert_called_once_with("not_exist")
