"""YelpSearchService 的单元测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock as Mock

import pytest

from backend.schemas.business import BusinessDetail, Category
from backend.services.yelp import YelpService
from backend.services.yelp_search import YelpSearchService


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

    def test_to_business_detail_full(self):
        biz = Mock()
        biz.id = "yelp_123"
        biz.alias = "test_alias"
        biz.name = "Test Restaurant"
        biz.image_url = "http://example.com/img.jpg"
        biz.is_closed = False
        biz.url = "http://example.com/biz"
        biz.review_count = 100
        biz.rating = 4.5
        biz.price = "$$"
        biz.categories = [
            Mock(alias="italian", title="Italian"),
            Mock(alias="pizza", title="Pizza"),
        ]
        biz.coordinates = Mock(latitude=40.7128, longitude=-74.0060)
        biz.location = Mock(
            address1="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            country="US",
            display_address=["123 Main St", "New York, NY 10001"],
        )
        biz.phone = "1234567890"
        biz.display_phone = "+1 123-456-7890"
        biz.transactions = Mock()
        biz.photos = Mock()
        biz.hours = Mock()

        result = YelpSearchService._to_business_detail(biz)
        assert isinstance(result, BusinessDetail)
        assert result.id == "yelp_123"
        assert result.name == "Test Restaurant"
        assert result.rating == 4.5
        assert result.price == "$$"
        assert len(result.categories) == 2
        assert result.categories[0] == Category(alias="italian", title="Italian")
        assert result.location is not None
        assert result.location.city == "New York"
        assert result.coordinates is not None
        assert result.coordinates.latitude == 40.7128

    def test_to_business_detail_minimal(self):
        biz = Mock()
        biz.id = "yelp_min"
        biz.alias = None
        biz.name = "Minimal"
        biz.image_url = None
        biz.is_closed = None
        biz.url = None
        biz.review_count = None
        biz.rating = None
        biz.price = None
        biz.categories = []
        biz.coordinates = None
        biz.location = None
        biz.phone = None
        biz.display_phone = None
        biz.transactions = []
        biz.photos = []
        biz.hours = None

        result = YelpSearchService._to_business_detail(biz)
        assert result.id == "yelp_min"
        assert result.name == "Minimal"
        assert result.image_url is None
        assert result.categories == []
        assert result.location is None
        assert result.coordinates is None
        assert result.transactions == []
        assert result.photos == []

    @pytest.mark.asyncio
    async def test_search_no_location_raises(self, yelp_search_service):
        with pytest.raises(ValueError, match="location"):
            await yelp_search_service.search_as_schema(keyword="sushi")

    @pytest.mark.asyncio
    async def test_search_with_location(self, yelp_search_service, mock_yelp_service):
        mock_response = Mock()
        mock_response.total = 1
        mock_response.businesses = []

        biz = Mock()
        biz.id = "yelp_1"
        biz.alias = ""
        biz.name = "Sushi Place"
        biz.image_url = None
        biz.is_closed = False
        biz.url = None
        biz.review_count = 0
        biz.rating = 0.0
        biz.price = None
        biz.categories = []
        biz.coordinates = None
        biz.location = None
        biz.phone = ""
        biz.display_phone = ""
        biz.transactions = []
        biz.photos = []
        biz.hours = None
        mock_response.businesses = [biz]

        mock_yelp_service.search_businesses.return_value = mock_response

        result = await yelp_search_service.search_as_schema(
            keyword="sushi", location="New York", limit=10, offset=0
        )
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].name == "Sushi Place"
        mock_yelp_service.search_businesses.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_lat_lng(self, yelp_search_service, mock_yelp_service):
        mock_response = Mock()
        mock_response.total = 0
        mock_response.businesses = []
        mock_yelp_service.search_businesses.return_value = mock_response

        result = await yelp_search_service.search_as_schema(
            keyword="pizza",
            latitude=40.7128,
            longitude=-74.0060,
            limit=5,
            offset=0,
        )
        assert result.total == 0
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_search_with_all_filters(
        self, yelp_search_service, mock_yelp_service
    ):
        mock_response = Mock()
        mock_response.total = 0
        mock_response.businesses = []
        mock_yelp_service.search_businesses.return_value = mock_response

        await yelp_search_service.search_as_schema(
            keyword="sushi",
            category="japanese",
            location="Tokyo",
            sort_by="review_count",
            price="2,3",
            limit=20,
            offset=10,
        )
        called_kwargs = mock_yelp_service.search_businesses.call_args.kwargs
        assert called_kwargs["term"] == "sushi"
        assert called_kwargs["categories"] == "japanese"
        assert called_kwargs["location"] == "Tokyo"
        assert called_kwargs["price"] == "2,3"
        assert called_kwargs["sort_by"] == "review_count"
