"""测试 YelpService —— 模拟 HTTP 请求，不实际调用 API。"""

from __future__ import annotations


import pytest

_FAKE_KEY = "test-fake-api-key"


@pytest.mark.asyncio
async def test_yelp_service_init():
    """YelpService 初始化时使用传入的 API key。"""
    from backend.services.yelp import YelpService

    svc = YelpService(api_key=_FAKE_KEY)
    assert svc._base_url == "https://api.yelp.com/v3"
    assert svc._headers["Authorization"] == f"Bearer {_FAKE_KEY}"


class TestYelpServiceMocked:
    """使用 pytest-httpx 模拟 HTTP 请求。"""

    SEARCH_RESPONSE = {
        "businesses": [
            {
                "id": "test-biz-1",
                "alias": "test-biz",
                "name": "Test Business",
                "location": {"display_address": ["123 Test St"]},
                "phone": "+1234567890",
                "display_phone": "(123) 456-7890",
                "coordinates": {"latitude": 40.0, "longitude": -74.0},
            }
        ],
        "total": 1,
        "region": {"center": {"latitude": 40.0, "longitude": -74.0}},
    }

    REVIEWS_RESPONSE = {
        "reviews": [
            {
                "id": "test-review-1",
                "url": "https://yelp.com/review/1",
                "text": "Amazing!",
                "rating": 5,
                "time_created": "2024-01-01 00:00:00",
                "user": {
                    "id": "user-1",
                    "profile_url": "https://yelp.com/user/1",
                    "name": "Tester",
                },
            }
        ],
        "total": 1,
        "possible_languages": ["en"],
    }

    DETAIL_RESPONSE = {
        "id": "test-biz-1",
        "alias": "test-biz",
        "name": "Test Business",
        "is_claimed": True,
        "photos": ["https://example.com/photo.jpg"],
        "location": {"display_address": ["123 Test St"]},
        "phone": "+1234567890",
        "display_phone": "(123) 456-7890",
        "coordinates": {"latitude": 40.0, "longitude": -74.0},
        "hours": {
            "open": [
                {
                    "is_overnight": False,
                    "start": "0900",
                    "end": "2100",
                    "day": 0,
                }
            ],
            "hours_type": "REGULAR",
            "is_open_now": True,
        },
    }

    @pytest.mark.asyncio
    async def test_search_businesses(self, httpx_mock):
        """模拟 Search API 调用，验证解析结果。"""
        httpx_mock.add_response(
            url="https://api.yelp.com/v3/businesses/search?location=New+York&limit=20&offset=0",
            json=self.SEARCH_RESPONSE,
        )
        from backend.services.yelp import YelpService

        svc = YelpService(api_key=_FAKE_KEY)
        result = await svc.search_businesses(location="New York")
        assert result.total == 1
        assert len(result.businesses) == 1
        assert result.businesses[0].name == "Test Business"

    @pytest.mark.asyncio
    async def test_get_business(self, httpx_mock):
        """模拟 Details API 调用。"""
        httpx_mock.add_response(
            url="https://api.yelp.com/v3/businesses/test-biz-1",
            json=self.DETAIL_RESPONSE,
        )
        from backend.services.yelp import YelpService

        svc = YelpService(api_key=_FAKE_KEY)
        biz = await svc.get_business("test-biz-1")
        assert biz.id == "test-biz-1"
        assert biz.is_claimed is True
        assert biz.hours is not None

    @pytest.mark.asyncio
    async def test_get_reviews(self, httpx_mock):
        """模拟 Reviews API 调用。"""
        httpx_mock.add_response(
            url="https://api.yelp.com/v3/businesses/test-biz-1/reviews?limit=20&offset=0",
            json=self.REVIEWS_RESPONSE,
        )
        from backend.services.yelp import YelpService

        svc = YelpService(api_key=_FAKE_KEY)
        result = await svc.get_reviews("test-biz-1")
        assert result.total == 1
        assert result.reviews[0].text == "Amazing!"

    @pytest.mark.asyncio
    async def test_api_error_raises_yelp_error(self, httpx_mock):
        """API 返回错误时抛出自定义异常。"""
        httpx_mock.add_response(
            url="https://api.yelp.com/v3/businesses/search?location=Nowhere&limit=20&offset=0",
            status_code=400,
            json={
                "error": {"code": "INVALID_REQUEST", "description": "Invalid location"}
            },
        )
        from backend.services.yelp import YelpError, YelpService

        svc = YelpService(api_key=_FAKE_KEY)
        with pytest.raises(YelpError) as excinfo:
            await svc.search_businesses(location="Nowhere")
        assert excinfo.value.status_code == 400
        assert excinfo.value.code == "INVALID_REQUEST"

    @pytest.mark.asyncio
    async def test_api_unauthorized(self, httpx_mock):
        """API Key 无效时返回 401。"""
        httpx_mock.add_response(
            url="https://api.yelp.com/v3/businesses/search?location=NYC&limit=20&offset=0",
            status_code=401,
            json={"error": {"code": "TOKEN_INVALID", "description": "Invalid API key"}},
        )
        from backend.services.yelp import YelpError, YelpService

        svc = YelpService(api_key=_FAKE_KEY)
        with pytest.raises(YelpError) as excinfo:
            await svc.search_businesses(location="NYC")
        assert excinfo.value.status_code == 401

    @pytest.mark.asyncio
    async def test_search_with_term_and_categories(self, httpx_mock):
        """搜索时传 term 和 categories 参数。"""
        httpx_mock.add_response(
            url="https://api.yelp.com/v3/businesses/search?location=NYC&term=pizza&categories=restaurants&limit=20&offset=0",
            json=self.SEARCH_RESPONSE,
        )
        from backend.services.yelp import YelpService

        svc = YelpService(api_key=_FAKE_KEY)
        result = await svc.search_businesses(
            location="NYC", term="pizza", categories="restaurants"
        )
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_error_without_description_fallback_to_text(self, httpx_mock):
        """错误 JSON 缺少 description 时 fallback 到 resp.text。"""
        httpx_mock.add_response(
            url="https://api.yelp.com/v3/businesses/search?location=ERR&limit=20&offset=0",
            status_code=500,
            json={"error": {"code": "SERVER_ERROR"}},
        )
        from backend.services.yelp import YelpError, YelpService

        svc = YelpService(api_key=_FAKE_KEY)
        with pytest.raises(YelpError) as excinfo:
            await svc.search_businesses(location="ERR")
        assert excinfo.value.status_code == 500
        assert excinfo.value.code == "SERVER_ERROR"


class TestYelpError:
    """YelpError 异常类。"""

    def test_construct(self):
        from backend.services.yelp import YelpError

        err = YelpError(status_code=400, code="BAD_REQUEST", description="bad")
        assert err.status_code == 400
        assert err.code == "BAD_REQUEST"
        assert err.description == "bad"
        assert "400" in str(err)
        assert "BAD_REQUEST" in str(err)

    def test_construct_with_unknown(self):
        from backend.services.yelp import YelpError

        err = YelpError(status_code=500, code="", description="")
        assert err.status_code == 500
