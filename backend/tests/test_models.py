"""ORM 模型基础测试（不依赖数据库）。"""

from __future__ import annotations


def test_business_repr():
    from backend.models.business import Business

    b = Business(id="b1", alias="b1", name="Test Biz")
    r = repr(b)
    assert "Business" in r
    assert "b1" in r
    assert "Test Biz" in r


def test_review_repr():
    from backend.models.review import Review

    rv = Review(
        id="r1", business_id="b1", text="OK", rating=3, time_created="2020-01-01"
    )
    r = repr(rv)
    assert "Review" in r
    assert "r1" in r
    assert "b1" in r


def test_user_repr():
    from backend.models.user import User

    u = User(id="u1", name="Alice")
    r = repr(u)
    assert "User" in r
    assert "u1" in r
    assert "Alice" in r
