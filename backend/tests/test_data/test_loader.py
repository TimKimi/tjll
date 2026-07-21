"""测试 data 模块的加载器转换函数。

测试字段映射是否正确：
  - _make_alias: 商家名称 → alias
  - _parse_categories: 逗号分隔字符串 → JSON 数组
  - _make_address: 地址字段 → JSON
  - _parse_hours: 营业时间格式转换
  - convert_business / convert_review: 完整数据行转换
"""

from __future__ import annotations

import json

from backend.data.loader import (
    _make_address,
    _make_alias,
    _parse_categories,
    _parse_hours,
    convert_business,
    convert_review,
)
from backend.data.schemas import DatasetBusiness, DatasetReview


# ============================================================
# _make_alias
# ============================================================


class TestMakeAlias:
    def test_simple_name(self):
        assert _make_alias("Garaje") == "garaje"

    def test_name_with_spaces(self):
        assert _make_alias("Golden Boy Pizza") == "golden-boy-pizza"

    def test_name_with_special_chars(self):
        # ampersand and accents stripped, only ascii alphanumeric kept
        result = _make_alias("Bistro & Grill")
        assert result == "bistro-grill"

    def test_name_with_unicode(self):
        # 全部非 ASCII 字符被移除后返回 fallback
        assert _make_alias("東京ラーメン") == "unknown"

    def test_strips_whitespace(self):
        assert _make_alias("  The  Shop  ") == "the-shop"

    def test_truncates_long_name(self):
        long_name = "a" * 300
        result = _make_alias(long_name)
        assert len(result) <= 255


# ============================================================
# _parse_categories
# ============================================================


class TestParseCategories:
    def test_single_category(self):
        result = _parse_categories("Mexican")
        assert result is not None
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["alias"] == "mexican"
        assert parsed[0]["title"] == "Mexican"

    def test_multiple_categories(self):
        result = _parse_categories("Mexican, Burgers, Gastropubs")
        assert result is not None
        parsed = json.loads(result)
        assert len(parsed) == 3
        assert parsed[0]["alias"] == "mexican"
        assert parsed[1]["alias"] == "burgers"
        assert parsed[2]["alias"] == "gastropubs"

    def test_empty_string_returns_none(self):
        assert _parse_categories("") is None
        assert _parse_categories("   ") is None

    def test_category_with_special_chars(self):
        """处理分类中的 & 和 / 符号。"""
        result = _parse_categories(
            "Traditional Chinese Medicine, Naturopathic/Holistic"
        )
        assert result is not None
        parsed = json.loads(result)
        assert parsed[0]["alias"] == "traditional-chinese-medicine"
        assert parsed[1]["alias"] == "naturopathic-holistic"

    def test_leading_trailing_spaces(self):
        result = _parse_categories("  Pizza ,  Tacos  ")
        assert result is not None
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["title"] == "Pizza"
        assert parsed[1]["title"] == "Tacos"


# ============================================================
# _make_address
# ============================================================


class TestMakeAddress:
    def test_full_address(self):
        result = _make_address("475 3rd St", "San Francisco", "CA", "94107")
        parsed = json.loads(result)
        assert parsed["address1"] == "475 3rd St"
        assert parsed["city"] == "San Francisco"
        assert parsed["state"] == "CA"
        assert parsed["zip_code"] == "94107"
        assert parsed["country"] == "US"
        assert len(parsed["display_address"]) == 2
        assert "San Francisco, CA 94107" in parsed["display_address"]

    def test_minimal_address(self):
        result = _make_address("1 Main St", "Town", "NY", "10001")
        parsed = json.loads(result)
        assert parsed["address1"] == "1 Main St"
        assert parsed["city"] == "Town"
        assert parsed["state"] == "NY"
        assert parsed["zip_code"] == "10001"


# ============================================================
# _parse_hours
# ============================================================


class TestParseHours:
    def test_typical_hours(self):
        hours = {
            "Monday": "9:0-18:0",
            "Tuesday": "9:0-18:0",
            "Wednesday": "9:0-18:0",
            "Thursday": "9:0-18:0",
            "Friday": "9:0-18:0",
            "Saturday": "10:0-14:0",
        }
        result = _parse_hours(hours)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["hours_type"] == "REGULAR"
        assert parsed["is_open_now"] is False
        assert len(parsed["open"]) == 6

        # Monday = day 1
        mon = [o for o in parsed["open"] if o["day"] == 1]
        assert len(mon) == 1
        assert mon[0]["start"] == "0900"
        assert mon[0]["end"] == "1800"

        # Sunday is not in the dict, so no entry with day=0
        sun = [o for o in parsed["open"] if o["day"] == 0]
        assert len(sun) == 0

    def test_null_hours_returns_none(self):
        assert _parse_hours(None) is None

    def test_empty_dict_returns_none(self):
        assert _parse_hours({}) is None

    def test_closed_day_skipped(self):
        """'0:0-0:0' 表示当天不营业，应跳过。"""
        hours = {
            "Monday": "0:0-0:0",
            "Tuesday": "9:0-17:0",
        }
        result = _parse_hours(hours)
        assert result is not None
        parsed = json.loads(result)
        assert len(parsed["open"]) == 1
        assert parsed["open"][0]["day"] == 2  # Tuesday

    def test_padded_time(self):
        """接受 HH:MM 格式（如 10:00）。"""
        hours = {"Monday": "10:00-21:00"}
        result = _parse_hours(hours)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["open"][0]["start"] == "1000"
        assert parsed["open"][0]["end"] == "2100"

    def test_all_days_present(self):
        """所有七天都营业时，检查日期映射。"""
        hours = {
            day: "9:0-17:0"
            for day in [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
        }
        result = _parse_hours(hours)
        assert result is not None
        parsed = json.loads(result)
        days = {o["day"] for o in parsed["open"]}
        assert days == {0, 1, 2, 3, 4, 5, 6}  # 0=Sunday ... 6=Saturday

    def test_skip_invalid_day_name(self):
        hours = {"InvalidDay": "9:0-17:0", "Monday": "9:0-17:0"}
        result = _parse_hours(hours)
        assert result is not None
        parsed = json.loads(result)
        assert len(parsed["open"]) == 1
        assert parsed["open"][0]["day"] == 1

    def test_malformed_time_skipped(self):
        hours = {"Monday": "not-a-time"}
        result = _parse_hours(hours)
        assert result is None


# ============================================================
# convert_business（完整商家转换）
# ============================================================


class TestConvertBusiness:
    def test_open_business(self):
        raw = DatasetBusiness(
            business_id="test-123",
            name="Golden Boy Pizza",
            address="123 Main St",
            city="Los Angeles",
            state="CA",
            postal_code="90001",
            latitude=34.05,
            longitude=-118.24,
            stars=4.0,
            review_count=500,
            is_open=1,
            categories="Pizza, Italian",
            hours={"Monday": "10:0-22:0"},
        )
        result = convert_business(raw)
        assert result.id == "test-123"
        assert result.name == "Golden Boy Pizza"
        assert result.alias == "golden-boy-pizza"
        assert result.rating == 4.0
        assert result.review_count == 500
        assert result.is_closed is False  # is_open=1 → is_closed=False
        assert result.latitude == 34.05
        assert result.longitude == -118.24

        # categories 被转为 JSON
        assert result.categories is not None
        cats = json.loads(result.categories)
        assert len(cats) == 2
        assert cats[0]["alias"] == "pizza"

        # address 被合并为 JSON
        assert result.address is not None
        addr = json.loads(result.address)
        assert addr["city"] == "Los Angeles"
        assert addr["state"] == "CA"

    def test_closed_business(self):
        raw = DatasetBusiness(
            business_id="closed-1",
            name="Closed Shop",
            address="1 St",
            city="C",
            state="S",
            postal_code="Z",
            is_open=0,
        )
        result = convert_business(raw)
        assert result.is_closed is True  # is_open=0 → is_closed=True

    def test_no_categories(self):
        raw = DatasetBusiness(
            business_id="no-cat",
            name="No Cat",
            address="1 St",
            city="C",
            state="S",
            postal_code="Z",
            is_open=1,
        )
        result = convert_business(raw)
        assert result.categories is None

    def test_no_hours(self):
        raw = DatasetBusiness(
            business_id="no-hours",
            name="No Hours",
            address="1 St",
            city="C",
            state="S",
            postal_code="Z",
            is_open=1,
        )
        result = convert_business(raw)
        assert result.hours is None


# ============================================================
# convert_review（完整评论转换）
# ============================================================


class TestConvertReview:
    def test_typical_review(self):
        raw = DatasetReview(
            review_id="rev-abc",
            user_id="user-123",
            business_id="biz-456",
            stars=4.0,
            date="2018-07-07 22:09:11",
            text="Great food!",
            useful=3,
            funny=1,
            cool=2,
        )
        result = convert_review(raw)
        assert result.id == "rev-abc"
        assert result.business_id == "biz-456"
        assert result.rating == 4  # float → int
        assert result.time_created == "2018-07-07 22:09:11"
        assert result.text == "Great food!"

        # user 被存为 JSON
        assert result.user is not None
        user = json.loads(result.user)
        assert user["id"] == "user-123"

    def test_low_rating(self):
        raw = DatasetReview(
            review_id="r-low",
            user_id="u1",
            business_id="b1",
            stars=1.0,
            date="2020-01-01",
            text="Terrible",
        )
        result = convert_review(raw)
        assert result.rating == 1

    def test_high_rating(self):
        raw = DatasetReview(
            review_id="r-high",
            user_id="u2",
            business_id="b2",
            stars=5.0,
            date="2020-01-01",
            text="Excellent",
        )
        result = convert_review(raw)
        assert result.rating == 5

    def test_no_user_id(self):
        """极少数情况下 user_id 可能为空。"""
        raw = DatasetReview(
            review_id="r-no-user",
            user_id="",
            business_id="b1",
            stars=3.0,
            date="2020-01-01",
            text="OK",
        )
        result = convert_review(raw)
        assert result.user is None
