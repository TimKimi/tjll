# backend/tests/api/test_yelp_search.py
"""YelpSearchService 的单元测试。"""

import pytest
from unittest.mock import AsyncMock, MagicMock as Mock

from backend.schemas.business import BusinessDetail, Category
from backend.schemas.common import PaginatedData
from backend.services.yelp_search import YelpSearchService
from backend.services.yelp import YelpService, YelpError


class TestYelpSearchService:
    """测试 YelpSearchService 类。"""

    @pytest.fixture
    def mock_yelp_service(self):
        mock = Mock(spec=YelpService)
        mock.search_businesses = AsyncMock()
        return mock

    @pytest.fixture
    def yelp_search_service(self, mock_yelp_service):
        return YelpSearchService(yelp_service=mock_yelp_service)

    # ---------- 测试 _to_business_detail ----------
    def test_to_business_detail_full(self):
        biz = Mock()
        biz.id = "yelp_123"
        biz.alias = "test_alias"
        biz.name = "Test Restaurant"
        biz.image_url = "http://img.jpg"
        biz.is_closed = False
        biz.url = "http://yelp.com/biz"
        biz.review_count = 42
        biz.rating = 4.5
        biz.price = "$$"

        cat1 = Mock()
        cat1.alias = "italian"
        cat1.title = "Italian"
        cat2 = Mock()
        cat2.alias = "pizza"
        cat2.title = "Pizza"
        biz.categories = [cat1, cat2]

        loc = Mock()
        loc.address1 = "123 Main St"
        loc.city = "New York"
        loc.state = "NY"
        loc.zip_code = "10001"
        loc.country = "US"
        loc.display_address = ["123 Main St", "New York, NY 10001"]
        biz.location = loc

        coords = Mock()
        coords.latitude = 40.7128
        coords.longitude = -74.0060
        biz.coordinates = coords

        biz.phone = "+123456789"
        biz.display_phone = "(123) 456-7890"
        biz.transactions = ["delivery", "pickup"]
        biz.photos = ["http://photo1.jpg", "http://photo2.jpg"]

        result = YelpSearchService._to_business_detail(biz)

        assert isinstance(result, BusinessDetail)
        assert result.id == "yelp_123"
        assert result.alias == "test_alias"
        assert result.name == "Test Restaurant"
        assert result.image_url == "http://img.jpg"
        assert result.is_closed is False
        assert result.url == "http://yelp.com/biz"
        assert result.review_count == 42
        assert result.rating == 4.5
        assert result.price == "$$"
        assert result.categories == [
            Category(alias="italian", title="Italian"),
            Category(alias="pizza", title="Pizza"),
        ]
        assert result.location is not None
        assert result.location.address1 == "123 Main St"
        assert result.location.city == "New York"
        assert result.coordinates is not None
        assert result.coordinates.latitude == 40.7128
        assert result.coordinates.longitude == -74.0060
        assert result.phone == "+123456789"
        assert result.display_phone == "(123) 456-7890"
        assert result.transactions == ["delivery", "pickup"]
        assert result.photos == ["http://photo1.jpg", "http://photo2.jpg"]
        assert result.hours is None

    def test_to_business_detail_minimal(self):
        biz = Mock()
        biz.id = "yelp_456"
        biz.alias = None
        biz.name = "Minimal"
        biz.image_url = None
        biz.is_closed = None
        biz.url = None
        biz.review_count = None
        biz.rating = None
        biz.price = None
        biz.categories = None
        biz.location = None
        biz.coordinates = None
        biz.phone = None
        biz.display_phone = None
        biz.transactions = None
        biz.photos = None

        result = YelpSearchService._to_business_detail(biz)
        assert result.id == "yelp_456"
        assert result.alias == ""
        assert result.name == "Minimal"
        assert result.image_url is None
        assert result.is_closed is False
        assert result.url is None
        assert result.review_count == 0
        assert result.rating == 0.0
        assert result.price is None
        assert result.categories == []
        assert result.location is None
        assert result.coordinates is None
        assert result.phone == ""
        assert result.display_phone == ""
        assert result.transactions == []
        assert result.photos == []
        assert result.hours is None

    # ---------- 测试 search_as_schema ----------
    @pytest.mark.asyncio
    async def test_search_as_schema_success(
        self, yelp_search_service, mock_yelp_service
    ):
        mock_result = Mock()
        biz = Mock()
        biz.id = "b1"
        biz.alias = "a1"
        biz.name = "Restaurant"
        biz.image_url = None
        biz.is_closed = False
        biz.url = None
        biz.review_count = 10
        biz.rating = 4.0
        biz.price = "$$"
        biz.categories = []
        biz.location = None
        biz.coordinates = None
        biz.phone = ""
        biz.display_phone = ""
        biz.transactions = []
        biz.photos = []
        mock_result.businesses = [biz]
        mock_result.total = 1
        mock_yelp_service.search_businesses.return_value = mock_result

        result = await yelp_search_service.search_as_schema(
            keyword="sushi", location="Tokyo", limit=5, offset=10, sort_by="rating"
        )

        mock_yelp_service.search_businesses.assert_called_once_with(
            limit=5, offset=10, location="Tokyo", term="sushi", sort_by="rating"
        )
        assert isinstance(result, PaginatedData)
        assert result.total == 1
        assert result.page == 3
        assert result.page_size == 5
        assert result.total_pages == 1
        assert len(result.items) == 1
        assert result.items[0].id == "b1"
        assert result.items[0].name == "Restaurant"

    @pytest.mark.asyncio
    async def test_search_as_schema_with_category(
        self, yelp_search_service, mock_yelp_service
    ):
        """测试传入 category 参数时正确传递到 Yelp API。"""
        mock_result = Mock()
        mock_result.businesses = []
        mock_result.total = 0
        mock_yelp_service.search_businesses.return_value = mock_result

        await yelp_search_service.search_as_schema(
            keyword="pizza",
            category="italian",
            location="NYC",
            limit=10,
            offset=0,
            sort_by="rating",
        )

        mock_yelp_service.search_businesses.assert_called_once_with(
            limit=10,
            offset=0,
            location="NYC",
            term="pizza",
            categories="italian",
            sort_by="rating",
        )

    @pytest.mark.asyncio
    async def test_search_as_schema_with_price_and_coords(
        self, yelp_search_service, mock_yelp_service
    ):
        mock_result = Mock()
        mock_result.businesses = []
        mock_result.total = 0
        mock_yelp_service.search_businesses.return_value = mock_result

        await yelp_search_service.search_as_schema(
            keyword="coffee",
            latitude=40.0,
            longitude=-75.0,
            price="1,2",
            limit=10,
            offset=0,
            sort_by="distance",
        )
        mock_yelp_service.search_businesses.assert_called_once_with(
            limit=10,
            offset=0,
            latitude=40.0,
            longitude=-75.0,
            term="coffee",
            price="1,2",
            sort_by="distance",
        )

    @pytest.mark.asyncio
    async def test_search_as_schema_missing_location(self, yelp_search_service):
        with pytest.raises(ValueError) as exc_info:
            await yelp_search_service.search_as_schema(
                keyword="sushi", location=None, latitude=None, longitude=None
            )
        assert "location" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_as_schema_missing_latitude_but_has_longitude(
        self, yelp_search_service
    ):
        with pytest.raises(ValueError) as exc_info:
            await yelp_search_service.search_as_schema(keyword="sushi", longitude=-74.0)
        assert "location" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_as_schema_has_location_only(
        self, yelp_search_service, mock_yelp_service
    ):
        mock_result = Mock()
        mock_result.businesses = []
        mock_result.total = 0
        mock_yelp_service.search_businesses.return_value = mock_result

        await yelp_search_service.search_as_schema(location="NYC")
        mock_yelp_service.search_businesses.assert_called_once_with(
            limit=10, offset=0, location="NYC", sort_by="rating"
        )

    @pytest.mark.asyncio
    async def test_search_as_schema_has_latitude_longitude(
        self, yelp_search_service, mock_yelp_service
    ):
        mock_result = Mock()
        mock_result.businesses = []
        mock_result.total = 0
        mock_yelp_service.search_businesses.return_value = mock_result

        await yelp_search_service.search_as_schema(latitude=40.0, longitude=-74.0)
        mock_yelp_service.search_businesses.assert_called_once_with(
            limit=10, offset=0, latitude=40.0, longitude=-74.0, sort_by="rating"
        )

    @pytest.mark.asyncio
    async def test_search_as_schema_yelp_error(
        self, yelp_search_service, mock_yelp_service
    ):
        mock_yelp_service.search_businesses.side_effect = YelpError(
            400, "BAD_REQUEST", "Invalid parameter"
        )

        with pytest.raises(YelpError) as exc_info:
            await yelp_search_service.search_as_schema(location="NYC")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_search_as_schema_handles_limit_gt_50(
        self, yelp_search_service, mock_yelp_service
    ):
        mock_result = Mock()
        mock_result.businesses = []
        mock_result.total = 0
        mock_yelp_service.search_businesses.return_value = mock_result

        await yelp_search_service.search_as_schema(location="NYC", limit=100)
        mock_yelp_service.search_businesses.assert_called_once_with(
            limit=50, offset=0, location="NYC", sort_by="rating"
        )

    @pytest.mark.asyncio
    async def test_search_as_schema_computes_pages_correctly(
        self, yelp_search_service, mock_yelp_service
    ):
        """测试分页计算正确。"""
        mock_businesses = []
        for _ in range(5):
            biz = Mock()
            biz.id = "b1"
            biz.alias = ""
            biz.name = "Restaurant"
            biz.image_url = None
            biz.is_closed = False
            biz.url = None
            biz.review_count = 10
            biz.rating = 4.0
            biz.price = "$$"
            biz.categories = []
            biz.location = None
            biz.coordinates = None
            biz.phone = ""
            biz.display_phone = ""
            biz.transactions = []
            biz.photos = []
            mock_businesses.append(biz)

        mock_result = Mock()
        mock_result.businesses = mock_businesses
        mock_result.total = 25
        mock_yelp_service.search_businesses.return_value = mock_result

        result = await yelp_search_service.search_as_schema(
            location="NYC", limit=10, offset=20
        )
        assert result.total == 25
        assert result.page == 3
        assert result.total_pages == 3
        assert len(result.items) == 5

        # 测试 total=0
        mock_result.total = 0
        mock_result.businesses = []
        result = await yelp_search_service.search_as_schema(
            location="NYC", limit=10, offset=0
        )
        assert result.total == 0
        assert result.page == 1
        assert result.total_pages == 0

        # 测试 total=5, limit=10
        mock_result.total = 5
        mock_result.businesses = mock_businesses[:5]
        result = await yelp_search_service.search_as_schema(
            location="NYC", limit=10, offset=0
        )
        assert result.total == 5
        assert result.page == 1
        assert result.total_pages == 1
