"""测试 data 模块的 Pydantic Schema 解析。

测试 DatasetBusiness / DatasetReview 能否正确解析
Yelp 学术数据集 JSON 格式，以及 Converted* 模型能否正确构造。
"""

from __future__ import annotations

from backend.data.schemas import (
    ConvertedBusiness,
    ConvertedReview,
    DatasetBusiness,
    DatasetReview,
)


class TestDatasetBusiness:
    """原始商家 JSONL 行解析。"""

    def test_parse_full(self):
        """能解析完整的商家数据。"""
        biz = DatasetBusiness(
            business_id="tnhfDv5Il8EaGSXZGiuQGg",
            name="Garaje",
            address="475 3rd St",
            city="San Francisco",
            state="CA",
            postal_code="94107",
            latitude=37.7817529521,
            longitude=-122.39612197,
            stars=4.5,
            review_count=1198,
            is_open=1,
            attributes={"RestaurantsTakeOut": True},
            categories="Mexican, Burgers, Gastropubs",
            hours={"Monday": "10:00-21:00", "Tuesday": "10:00-21:00"},
        )
        assert biz.business_id == "tnhfDv5Il8EaGSXZGiuQGg"
        assert biz.name == "Garaje"
        assert biz.city == "San Francisco"
        assert biz.stars == 4.5
        assert biz.review_count == 1198
        assert biz.is_open == 1
        assert biz.categories is not None
        assert "Mexican" in biz.categories
        assert biz.hours is not None
        assert biz.hours["Monday"] == "10:00-21:00"

    def test_parse_minimal(self):
        """可选字段缺失时使用默认值。"""
        biz = DatasetBusiness(
            business_id="test-id",
            name="Test",
            address="123 St",
            city="City",
            state="CA",
            postal_code="12345",
            stars=0.0,
            review_count=0,
            is_open=0,
        )
        assert biz.business_id == "test-id"
        assert biz.latitude is None  # 默认为 None
        assert biz.stars == 0.0
        assert biz.review_count == 0
        assert biz.is_open == 0
        assert biz.attributes is None
        assert biz.categories is None
        assert biz.hours is None

    def test_is_open_int_bool(self):
        """is_open 接受 0/1 整数。"""
        biz_open = DatasetBusiness(
            business_id="a",
            name="A",
            address="1",
            city="C",
            state="S",
            postal_code="Z",
            is_open=1,
        )
        biz_closed = DatasetBusiness(
            business_id="b",
            name="B",
            address="2",
            city="C",
            state="S",
            postal_code="Z",
            is_open=0,
        )
        assert biz_open.is_open == 1
        assert biz_closed.is_open == 0


class TestDatasetReview:
    """原始评论 JSONL 行解析。"""

    def test_parse_full(self):
        """能解析完整的评论数据。"""
        rev = DatasetReview(
            review_id="zdSx_SD6obEhz9VrW9uAWA",
            user_id="Ha3iJu77CxlrFm-vQRs_8g",
            business_id="tnhfDv5Il8EaGSXZGiuQGg",
            stars=4.0,
            date="2016-03-09",
            text="Great place to hang out after work!",
            useful=5,
            funny=2,
            cool=3,
        )
        assert rev.review_id == "zdSx_SD6obEhz9VrW9uAWA"
        assert rev.user_id == "Ha3iJu77CxlrFm-vQRs_8g"
        assert rev.business_id == "tnhfDv5Il8EaGSXZGiuQGg"
        assert rev.stars == 4.0
        assert rev.date == "2016-03-09"
        assert "Great place" in rev.text
        assert rev.useful == 5
        assert rev.funny == 2
        assert rev.cool == 3

    def test_parse_float_stars(self):
        """实际数据中 stars 是浮点数，应能被解析。"""
        rev = DatasetReview(
            review_id="r123",
            user_id="u456",
            business_id="b789",
            stars=3.0,
            date="2018-07-07 22:09:11",
            text="OK",
        )
        assert rev.stars == 3.0
        assert isinstance(rev.stars, float)

    def test_defaults_missing_fields(self):
        """可选字段缺失时使用默认值。"""
        rev = DatasetReview(
            review_id="r1",
            user_id="u1",
            business_id="b1",
            stars=5.0,
            date="2020-01-01",
            text="Good",
        )
        assert rev.useful == 0
        assert rev.funny == 0
        assert rev.cool == 0


class TestConvertedBusiness:
    """转换后的商家数据模型。"""

    def test_construct_full(self):
        """能构造完整的转换后商家。"""
        biz = ConvertedBusiness(
            id="biz-1",
            alias="test-biz",
            name="Test Business",
            is_closed=False,
            review_count=100,
            rating=4.5,
            categories='[{"alias":"mexican","title":"Mexican"}]',
            latitude=37.78,
            longitude=-122.39,
            address='{"city":"San Francisco"}',
            phone="+1234567890",
        )
        assert biz.id == "biz-1"
        assert biz.alias == "test-biz"
        assert biz.name == "Test Business"
        assert biz.rating == 4.5
        assert biz.review_count == 100
        assert biz.is_closed is False
        assert biz.latitude == 37.78
        assert biz.categories is not None
        assert "Mexican" in biz.categories

    def test_defaults(self):
        """可选字段的默认值。"""
        biz = ConvertedBusiness(
            id="biz-2",
            alias="b",
            name="B",
        )
        assert biz.image_url is None
        assert biz.price is None
        assert biz.categories is None
        assert biz.latitude is None
        assert biz.hours is None
        assert biz.transactions is None
        assert biz.photos is None


class TestConvertedReview:
    """转换后的评论数据模型。"""

    def test_construct(self):
        rev = ConvertedReview(
            id="rev-1",
            business_id="biz-1",
            text="Great food!",
            rating=5,
            time_created="2016-03-09",
            user='{"id": "user-1"}',
        )
        assert rev.id == "rev-1"
        assert rev.business_id == "biz-1"
        assert rev.text == "Great food!"
        assert rev.rating == 5
        assert rev.time_created == "2016-03-09"
        assert "user-1" in (rev.user or "")

    def test_user_optional(self):
        """user 字段可为 None。"""
        rev = ConvertedReview(
            id="rev-2",
            business_id="biz-2",
            text="OK",
            rating=3,
            time_created="2020-01-01",
        )
        assert rev.user is None
