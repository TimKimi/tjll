"""测试 User 模型、Schema、转换函数。"""

from __future__ import annotations

from backend.data.loader import convert_user
from backend.data.schemas import ConvertedUser, DatasetUser


class TestDatasetUser:
    """原始用户 JSONL 行解析。"""

    def test_parse_full(self):
        u = DatasetUser(
            user_id="Ha3iJu77CxlrFm-vQRs_8g",
            name="Sebastien",
            review_count=56,
            yelping_since="2011-01-01 16:47:26",
            useful=21,
            funny=88,
            cool=15,
            fans=1032,
            elite="2012,2013",
            friends="u1, u2, u3",
        )
        assert u.user_id == "Ha3iJu77CxlrFm-vQRs_8g"
        assert u.name == "Sebastien"
        assert u.yelping_since == "2011-01-01 16:47:26"
        assert len(u.yelping_since) == 19  # YYYY-MM-DD HH:MM:SS
        assert u.elite == "2012,2013"
        assert u.friends == "u1, u2, u3"


class TestConvertedUser:
    """转换后的用户数据模型。"""

    def test_construct(self):
        u = ConvertedUser(
            id="user-1",
            name="Alice",
            review_count=10,
            yelping_since="2015-06-01 12:00:00",
        )
        assert u.id == "user-1"
        assert u.name == "Alice"
        assert u.yelping_since == "2015-06-01 12:00:00"

    def test_elite_and_friends_raw_strings(self):
        """elite 和 friends 存为原始字符串，不应被 JSON 编码。"""
        u = ConvertedUser(
            id="user-2",
            name="Bob",
            elite="2010,2011,2012",
            friends="friend1, friend2",
        )
        # 验证 elite 是原始字符串，而不是 JSON 编码的
        assert u.elite == "2010,2011,2012"
        assert '"2010,2011,2012"' != u.elite  # 不是 JSON 双引号包裹

    def test_optional_fields_none(self):
        u = ConvertedUser(id="u3", name="C")
        assert u.elite is None
        assert u.friends is None


class TestConvertUser:
    """convert_user 函数测试。"""

    def test_typical_conversion(self):
        raw = DatasetUser(
            user_id="user-1",
            name="Alice",
            review_count=10,
            yelping_since="2015-06-01 12:00:00",
            useful=5,
            funny=3,
            cool=2,
            fans=100,
            average_stars=4.5,
            elite="2015,2016",
            friends="f1, f2, f3",
        )
        result = convert_user(raw)
        assert result.id == "user-1"
        assert result.name == "Alice"
        assert result.yelping_since == "2015-06-01 12:00:00"
        assert result.elite == "2015,2016"  # 原始字符串
        assert result.friends == "f1, f2, f3"  # 原始字符串

    def test_yelping_since_full_timestamp(self):
        """yelping_since 接受完整时间戳。"""
        raw = DatasetUser(
            user_id="u2",
            name="B",
            yelping_since="2008-11-16 05:10:49",
        )
        result = convert_user(raw)
        assert result.yelping_since == "2008-11-16 05:10:49"

    def test_empty_elite_friends_become_none(self):
        raw = DatasetUser(
            user_id="u3",
            name="C",
            yelping_since="2010-01-01",
            elite="",
            friends="",
        )
        result = convert_user(raw)
        assert result.elite is None
        assert result.friends is None

    def test_long_friends_string(self):
        """friends 字段可能非常长（数千字符）。"""
        friends_list = [f"user_{i}" for i in range(100)]
        friends_str = ", ".join(friends_list)
        raw = DatasetUser(
            user_id="u4",
            name="D",
            yelping_since="2010-01-01",
            friends=friends_str,
        )
        result = convert_user(raw)
        assert result.friends is not None
        assert len(result.friends) > 500
        assert "user_0" in result.friends
        assert "user_99" in result.friends
