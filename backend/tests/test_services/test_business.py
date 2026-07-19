"""店铺服务层单元测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
        assert schema.location is not None
        assert schema.location.address1 is None
        assert schema.location.city is None
        assert schema.categories == []
        assert schema.transactions == []
        assert schema.photos == []
        assert schema.hours is None


# ---------- Fixtures ----------
@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    return db


@pytest.fixture
def sample_business():
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


class TestBusinessService:
    """测试 BusinessService 的所有方法。"""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, mock_db, sample_business):
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
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock

        service = BusinessService(mock_db)
        result = await service.get_by_id("not_exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_businesses_default_source_db(self, mock_db, sample_business):
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
            assert result.total == 1
            assert result.items[0].id == "yelp_biz_1"
            assert result.items[0].name == "Yelp 餐厅"

    @pytest.mark.asyncio
    async def test_list_businesses_source_yelp_error(self, mock_db):
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
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        main_result = MagicMock()
        main_result.scalars.return_value.all.return_value = [sample_business]
        mock_db.execute.side_effect = [count_result, main_result]

        query = BusinessListQuery(keyword="餐厅")
        service = BusinessService(mock_db)
        result = await service.list_businesses(query)
        assert result.total == 1
