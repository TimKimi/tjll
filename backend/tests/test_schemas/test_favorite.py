"""Favorite 请求/响应 Schema 单元测试。"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.schemas.favorite import AddFavoriteRequest, FavoriteItem


class TestAddFavoriteRequest:
    """测试添加收藏请求 Schema。"""

    def test_valid(self):
        """合法请求。"""
        req = AddFavoriteRequest(shop_id="biz_001")
        assert req.shop_id == "biz_001"

    def test_shop_id_required(self):
        """shop_id 是必填字段。"""
        with pytest.raises(ValidationError):
            AddFavoriteRequest()  # type: ignore

    def test_shop_id_cannot_be_empty(self):
        """shop_id 不能为空字符串。"""
        with pytest.raises(ValidationError):
            AddFavoriteRequest(shop_id="")


class TestFavoriteItem:
    """测试收藏项响应 Schema。"""

    def test_valid_minimal(self):
        """仅用必填字段创建。"""
        now = datetime(2026, 7, 19, 15, 0, 0)
        item = FavoriteItem(
            id="fav_001", shop_id="biz_001", source="db", created_at=now
        )
        assert item.id == "fav_001"
        assert item.shop_id == "biz_001"
        assert item.name == ""
        assert item.image_url == ""
        assert item.rating == 0.0
        assert item.price == ""
        assert item.address == ""
        assert item.category == ""
        assert item.created_at == now

    def test_valid_full(self):
        """使用所有字段创建。"""
        now = datetime(2026, 7, 19, 15, 0, 0)
        item = FavoriteItem(
            id="fav_001",
            shop_id="biz_001",
            name="蜀九香火锅",
            image_url="https://example.com/shop1.jpg",
            rating=4.8,
            price="$$",
            address="锦江区春熙路88号",
            category="火锅",
            created_at=now,
        )
        assert item.name == "蜀九香火锅"
        assert item.image_url == "https://example.com/shop1.jpg"
        assert item.rating == 4.8
        assert item.price == "$$"
        assert item.category == "火锅"

    def test_id_required(self):
        """id 是必填字段。"""
        with pytest.raises(ValidationError):
            FavoriteItem(shop_id="biz_001", source="db", created_at=datetime.now())  # type: ignore

    def test_shop_id_required(self):
        """shop_id 是必填字段。"""
        with pytest.raises(ValidationError):
            FavoriteItem(id="fav_001", source="db", created_at=datetime.now())  # type: ignore

    def test_created_at_required(self):
        """created_at 是必填字段。"""
        with pytest.raises(ValidationError):
            FavoriteItem(id="fav_001", shop_id="biz_001", source="db")  # type: ignore
