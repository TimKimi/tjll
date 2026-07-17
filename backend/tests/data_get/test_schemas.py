"""测试 Pydantic Schema —— 从 Yelp API 示例 JSON 解析。"""

from __future__ import annotations

from backend.schemas.yelp import (
    YelpBusiness,
    YelpBusinessHours,
    YelpBusinessSearchResponse,
    YelpCategory,
    YelpCoordinates,
    YelpLocation,
    YelpOpenHour,
    YelpReview,
    YelpReviewUser,
    YelpReviewsResponse,
)


class TestYelpCategory:
    """分类模型解析。"""

    def test_from_dict(self):
        cat = YelpCategory(alias="pizza", title="Pizza")
        assert cat.alias == "pizza"
        assert cat.title == "Pizza"


class TestYelpCoordinates:
    """坐标模型解析。"""

    def test_from_dict(self):
        coord = YelpCoordinates(latitude=41.7873, longitude=-123.0515)
        assert coord.latitude == 41.7873
        assert coord.longitude == -123.0515


class TestYelpLocation:
    """地址模型解析。"""

    def test_from_dict_full(self):
        loc = YelpLocation(
            address1="350 5th Ave",
            address2="Suite 100",
            address3="",
            city="New York",
            state="NY",
            zip_code="10118",
            country="US",
            display_address=[
                "350 5th Ave",
                "Suite 100",
                "New York, NY 10118",
            ],
        )
        assert loc.city == "New York"
        assert loc.state == "NY"
        assert len(loc.display_address) == 3

    def test_from_dict_minimal(self):
        loc = YelpLocation(display_address=["New York, NY 10118"])
        assert loc.city is None
        assert loc.display_address == ["New York, NY 10118"]


class TestYelpBusiness:
    """商家模型解析 — 模拟 API 真实返回。"""

    def test_parse_search_result(self):
        """能正确解析 Search 接口返回的商家数据。"""
        biz = YelpBusiness(
            id="QPOI0dYeAl3U8iPM_IYWnA",
            alias="golden-boy-pizza-hamburg",
            name="Golden Boy Pizza",
            image_url="https://example.com/photo.jpg",
            is_closed=False,
            url="https://www.yelp.com/biz/golden-boy-pizza-hamburg",
            review_count=903,
            categories=[
                YelpCategory(alias="pizza", title="Pizza"),
                YelpCategory(alias="food", title="Food"),
            ],
            rating=4.0,
            coordinates=YelpCoordinates(latitude=41.7873, longitude=-123.0515),
            transactions=["pickup", "delivery"],
            price="$",
            location=YelpLocation(
                address1="James",
                address2="",
                address3="",
                city="Los Angeles",
                state="CA",
                zip_code="22399",
                country="US",
                display_address=["James", "Los Angeles, CA 22399"],
            ),
            phone="+14159829738",
            display_phone="(415) 982-9738",
            distance=4992.44,
            business_hours=None,
        )
        assert biz.id == "QPOI0dYeAl3U8iPM_IYWnA"
        assert biz.name == "Golden Boy Pizza"
        assert biz.rating == 4.0
        assert biz.review_count == 903
        assert len(biz.categories) == 2
        assert biz.categories[0].alias == "pizza"
        assert biz.coordinates is not None
        assert biz.coordinates.latitude == 41.7873
        assert biz.price == "$"
        assert biz.location is not None
        assert biz.location.city == "Los Angeles"

    def test_parse_detail_response(self):
        """能正确解析 Details 接口返回的额外字段。"""
        biz = YelpBusiness(
            id="QPOI0dYeAl3U8iPM_IYWnA",
            alias="golden-boy-pizza-hamburg",
            name="Golden Boy Pizza",
            image_url="https://example.com/photo.jpg",
            is_closed=False,
            url="https://www.yelp.com/biz/golden-boy-pizza-hamburg",
            review_count=903,
            categories=[
                YelpCategory(alias="pizza", title="Pizza"),
                YelpCategory(alias="food", title="Food"),
            ],
            rating=4.0,
            coordinates=YelpCoordinates(latitude=41.7873, longitude=-123.0515),
            transactions=["pickup", "delivery"],
            price="$",
            location=YelpLocation(
                address1="James",
                address2="",
                address3="",
                city="Los Angeles",
                state="CA",
                zip_code="22399",
                country="US",
                display_address=["James", "Los Angeles, CA 22399"],
            ),
            phone="+14159829738",
            display_phone="(415) 982-9738",
            distance=4992.44,
            is_claimed=True,
            photos=[
                "https://example.com/photo1.jpg",
                "https://example.com/photo2.jpg",
            ],
            business_hours=YelpBusinessHours(
                open=[
                    YelpOpenHour(
                        is_overnight=False,
                        start="0900",
                        end="2100",
                        day=0,
                    )
                ],
                hours_type="REGULAR",
                is_open_now=True,
            ),
        )
        assert biz.is_claimed is True
        assert len(biz.photos) == 2
        assert biz.hours is not None
        assert biz.hours.is_open_now is True
        assert biz.hours.open[0].start == "0900"

    def test_defaults_for_missing_fields(self):
        """缺少可选字段时，使用默认值。"""
        biz = YelpBusiness(
            id="test-id-123",
            alias="test-alias",
            name="Test Biz",
            location=YelpLocation(display_address=["Test Address"]),
            phone="",
            display_phone="",
            coordinates=YelpCoordinates(latitude=0.0, longitude=0.0),
            business_hours=None,
        )
        assert biz.id == "test-id-123"
        assert biz.rating == 0.0
        assert biz.review_count == 0
        assert biz.is_closed is False
        assert biz.categories == []

    def test_hours_normalized_from_list(self):
        """hours 字段是 list 时取第一个。"""
        biz = YelpBusiness.model_validate(
            {
                "id": "b",
                "alias": "b",
                "name": "B",
                "location": {"display_address": ["A"]},
                "phone": "",
                "display_phone": "",
                "coordinates": {"latitude": 0.0, "longitude": 0.0},
                "business_hours": [
                    {
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
                    {
                        "open": [
                            {
                                "is_overnight": False,
                                "start": "0900",
                                "end": "2100",
                                "day": 0,
                            }
                        ],
                        "hours_type": "REGULAR",
                        "is_open_now": False,
                    },
                ],
            }
        )
        assert biz.hours is not None
        assert biz.hours.is_open_now is True  # 取 list 第一个

    def test_hours_normalized_from_empty_list(self):
        """hours 是空 list 时返回 None。"""
        biz = YelpBusiness.model_validate(
            {
                "id": "b",
                "alias": "b",
                "name": "B",
                "location": {"display_address": ["A"]},
                "phone": "",
                "display_phone": "",
                "coordinates": {"latitude": 0.0, "longitude": 0.0},
                "business_hours": [],
            }
        )
        assert biz.hours is None


class TestYelpBusinessSearchResponse:
    """搜索响应整体解析。"""

    def test_parse_response(self):
        resp = YelpBusinessSearchResponse(
            businesses=[
                YelpBusiness(
                    id="biz-1",
                    alias="biz-one",
                    name="Biz One",
                    location=YelpLocation(display_address=["Addr1"]),
                    phone="123",
                    display_phone="123",
                    coordinates=YelpCoordinates(latitude=0.0, longitude=0.0),
                    business_hours=None,
                ),
                YelpBusiness(
                    id="biz-2",
                    alias="biz-two",
                    name="Biz Two",
                    location=YelpLocation(display_address=["Addr2"]),
                    phone="456",
                    display_phone="456",
                    coordinates=YelpCoordinates(latitude=1.0, longitude=1.0),
                    business_hours=None,
                ),
            ],
            total=100,
            region={"center": {"latitude": 40.0, "longitude": -74.0}},
        )
        assert resp.total == 100
        assert len(resp.businesses) == 2
        assert resp.businesses[0].name == "Biz One"
        assert resp.businesses[1].name == "Biz Two"


class TestYelpReview:
    """评论模型解析。"""

    def test_parse_review(self):
        review = YelpReview(
            id="review-abc",
            url="https://www.yelp.com/biz/xxx",
            text="Great food! Highly recommended.",
            rating=5,
            time_created="2016-08-29 00:41:13",
            user=YelpReviewUser(
                id="user-123",
                profile_url="https://example.com/user",
                image_url="https://example.com/avatar.jpg",
                name="Ella A.",
            ),
        )
        assert review.id == "review-abc"
        assert review.rating == 5
        assert review.text == "Great food! Highly recommended."
        assert review.user.name == "Ella A."
        assert review.user.profile_url == "https://example.com/user"

    def test_user_without_image(self):
        review = YelpReview(
            id="review-abc",
            url="https://www.yelp.com/biz/xxx",
            text="Great food! Highly recommended.",
            rating=5,
            time_created="2016-08-29 00:41:13",
            user=YelpReviewUser(
                id="user-123",
                profile_url="https://example.com/user",
                image_url=None,
                name="Ella A.",
            ),
        )
        assert review.user.image_url is None


class TestStoredBusiness:
    """StoredBusiness 模型。"""

    def test_from_yelp(self):
        from backend.schemas.yelp import StoredBusiness

        biz = YelpBusiness(
            id="b-1",
            alias="test",
            name="Test",
            location=YelpLocation(display_address=["Addr"]),
            phone="123",
            display_phone="123",
            coordinates=YelpCoordinates(latitude=1.0, longitude=2.0),
            business_hours=None,
        )
        stored = StoredBusiness.from_yelp(biz)
        assert stored.yelp_id == "b-1"
        assert stored.name == "Test"
        assert stored.coordinates is not None
        assert stored.coordinates.latitude == 1.0


class TestStoredReview:
    """StoredReview 模型。"""

    def test_from_yelp(self):
        from backend.schemas.yelp import StoredReview

        review = YelpReview(
            id="r-1",
            url="https://r.com/1",
            text="Good",
            rating=4,
            time_created="2020-01-01",
            user=YelpReviewUser(id="u1", profile_url="https://u.com/1", name="Alice"),
        )
        stored = StoredReview.from_yelp(review, business_id="b-1")
        assert stored.id == "r-1"
        assert stored.business_id == "b-1"
        assert stored.user.name == "Alice"


class TestYelpReviewsResponse:
    """评论响应整体解析。"""

    def test_parse_response(self):
        resp = YelpReviewsResponse(
            reviews=[
                YelpReview(
                    id="r1",
                    url="https://yelp.com/r1",
                    text="Good",
                    rating=4,
                    time_created="2020-01-01 12:00:00",
                    user=YelpReviewUser(
                        id="u1",
                        profile_url="https://yelp.com/u1",
                        name="Alice",
                    ),
                ),
                YelpReview(
                    id="r2",
                    url="https://yelp.com/r2",
                    text="Bad",
                    rating=1,
                    time_created="2020-02-01 12:00:00",
                    user=YelpReviewUser(
                        id="u2",
                        profile_url="https://yelp.com/u2",
                        name="Bob",
                    ),
                ),
            ],
            total=2,
            possible_languages=["en"],
        )
        assert resp.total == 2
        assert len(resp.reviews) == 2
        assert resp.reviews[0].rating == 4
        assert resp.reviews[1].rating == 1
        assert resp.possible_languages == ["en"]
