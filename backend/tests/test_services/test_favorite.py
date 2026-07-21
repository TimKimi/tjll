"""Favorite 服务层单元测试。"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


class TestListFavorites:
    """测试获取收藏列表。"""

    @pytest.mark.asyncio
    async def test_list_favorites_empty(self, mock_db):
        """空收藏列表应返回空列表。"""
        from backend.services.favorite import FavoriteService

        # Mock 查询收藏总数返回 0
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        # Mock 查询收藏列表返回空
        list_result = MagicMock()
        list_result.all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[count_result, list_result])

        service = FavoriteService(mock_db)
        result = await service.list_favorites("u_test", page=1, page_size=20)

        assert result.total == 0
        assert result.items == []
        assert result.page == 1
        assert result.page_size == 20
        assert result.total_pages == 0

    @pytest.mark.asyncio
    async def test_list_favorites_with_items(self, mock_db):
        """收藏列表返回收藏项和分页信息。"""
        from backend.services.favorite import FavoriteService

        # Mock 总数
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2

        # Mock 收藏列表（Favorite ORM 对象 + Business 字段的 tuple）
        fav1 = MagicMock()
        fav1.id = "fav_001"
        fav1.shop_id = "biz_001"
        fav1.source = "db"
        fav1.created_at = datetime(2026, 7, 19, 15, 0, 0)

        fav2 = MagicMock()
        fav2.id = "fav_002"
        fav2.shop_id = "biz_002"
        fav2.source = "db"
        fav2.created_at = datetime(2026, 7, 20, 10, 30, 0)

        # Row tuples returned by the join query
        row1 = (
            fav1,
            "蜀九香火锅",
            "https://example.com/shop1.jpg",
            4.8,
            "$$",
            '{"address1":"锦江区春熙路88号"}',
            '[{"alias":"hotpot","title":"火锅"}]',
        )
        row2 = (
            fav2,
            "必胜客",
            "https://example.com/shop2.jpg",
            3.5,
            "$",
            '{"address1":"武侯区科华北路"}',
            '[{"alias":"pizza","title":"披萨"}]',
        )

        list_result = MagicMock()
        list_result.all.return_value = [row1, row2]

        mock_db.execute = AsyncMock(side_effect=[count_result, list_result])

        service = FavoriteService(mock_db)
        result = await service.list_favorites("u_test", page=1, page_size=20)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.items[0].id == "fav_001"
        assert result.items[0].shop_id == "biz_001"
        assert result.items[0].name == "蜀九香火锅"
        assert result.items[0].image_url == "https://example.com/shop1.jpg"
        assert result.items[0].rating == 4.8
        assert result.items[0].price == "$$"
        assert result.items[0].address == "锦江区春熙路88号"
        assert result.items[0].category == "火锅"
        assert result.items[1].name == "必胜客"
        assert result.items[1].category == "披萨"
        assert result.total_pages == 1

    @pytest.mark.asyncio
    async def test_list_favorites_pagination(self, mock_db):
        """分页参数应正确传递。"""
        from backend.services.favorite import FavoriteService

        count_result = MagicMock()
        count_result.scalar_one.return_value = 25
        list_result = MagicMock()
        list_result.all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[count_result, list_result])

        service = FavoriteService(mock_db)
        result = await service.list_favorites("u_test", page=3, page_size=10)

        assert result.page == 3
        assert result.page_size == 10
        assert result.total_pages == 3  # 25/10 = 2.5 → 3


class TestAddFavorite:
    """测试添加收藏。"""

    @pytest.mark.asyncio
    async def test_add_favorite_success(self, mock_db):
        """添加收藏成功应返回收藏项信息。"""
        from backend.services.favorite import FavoriteService

        # Mock 商家存在
        mock_biz = MagicMock()
        mock_biz.name = "蜀九香火锅"
        mock_biz.image_url = "https://example.com/shop1.jpg"
        mock_biz.rating = 4.8
        mock_biz.price = "$$"
        mock_biz.address = '{"address1":"锦江区春熙路88号"}'
        mock_biz.categories = '[{"alias":"hotpot","title":"火锅"}]'

        biz_result = MagicMock()
        biz_result.scalar_one_or_none.return_value = mock_biz

        # Mock 未收藏（查重返回 None）
        fav_result = MagicMock()
        fav_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(side_effect=[biz_result, fav_result])

        # refresh 时设置 created_at
        now = datetime(2026, 7, 19, 15, 0, 0)

        async def _refresh_side_effect(obj):
            obj.created_at = now

        mock_db.refresh = AsyncMock(side_effect=_refresh_side_effect)

        service = FavoriteService(mock_db)
        result = await service.add_favorite("u_test", "biz_001")

        assert result.shop_id == "biz_001"
        assert result.name == "蜀九香火锅"
        assert result.rating == 4.8
        assert result.price == "$$"
        assert result.category == "火锅"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_favorite_shop_not_found(self, mock_db):
        """商家不存在应抛出异常。"""
        from backend.core.exceptions import AppError
        from backend.services.favorite import FavoriteService

        biz_result = MagicMock()
        biz_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(return_value=biz_result)

        service = FavoriteService(mock_db)
        with pytest.raises(AppError) as exc:
            await service.add_favorite("u_test", "nonexistent_biz")
        assert exc.value.code == 404
        assert "商家不存在" in exc.value.message

    @pytest.mark.asyncio
    async def test_add_favorite_duplicate(self, mock_db):
        """重复收藏应抛出异常。"""
        from backend.core.exceptions import AppError
        from backend.services.favorite import FavoriteService

        biz_result = MagicMock()
        biz_result.scalar_one_or_none.return_value = MagicMock()

        fav_result = MagicMock()
        fav_result.scalar_one_or_none.return_value = MagicMock()

        # add_favorite 先查商家，再查收藏，所以要给两个结果
        biz_result = MagicMock()
        biz_result.scalar_one_or_none.return_value = MagicMock()

        mock_db.execute = AsyncMock(side_effect=[biz_result, fav_result])

        service = FavoriteService(mock_db)
        with pytest.raises(AppError) as exc:
            await service.add_favorite("u_test", "biz_001")
        assert exc.value.code == 409
        assert "已收藏" in exc.value.message


class TestAddFavoriteYelpSource:
    """测试 Yelp 来源的收藏添加。"""

    @patch("backend.services.favorite.YelpService")
    @pytest.mark.asyncio
    async def test_add_yelp_favorite_success(self, mock_yelp_class, mock_db):
        """Yelp 来源收藏成功应返回收藏项信息。"""
        from backend.services.favorite import FavoriteService

        # Mock Yelp API 返回商家信息
        mock_yelp_instance = mock_yelp_class.return_value
        mock_biz = MagicMock()
        mock_biz.id = "yelp_biz_001"
        mock_biz.name = "Yelp Restaurant"
        mock_biz.image_url = "https://yelp.com/photo.jpg"
        mock_biz.rating = 4.5
        mock_biz.price = "$$$"
        mock_loc = MagicMock()
        mock_loc.address1 = "123 Main St"
        mock_biz.location = mock_loc
        mock_cat = MagicMock()
        mock_cat.alias = "italian"
        mock_cat.title = "Italian"
        mock_biz.categories = [mock_cat]
        mock_yelp_instance.get_business = AsyncMock(return_value=mock_biz)

        # Mock 未收藏
        fav_result = MagicMock()
        fav_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(return_value=fav_result)

        now = datetime(2026, 7, 21, 12, 0, 0)

        async def _refresh_side_effect(obj):
            obj.created_at = now

        mock_db.refresh = AsyncMock(side_effect=_refresh_side_effect)

        service = FavoriteService(mock_db)
        result = await service.add_favorite("u_test", "yelp_biz_001", source="yelp")

        assert result.shop_id == "yelp_biz_001"
        assert result.source == "yelp"
        assert result.name == "Yelp Restaurant"
        assert result.rating == 4.5
        assert result.price == "$$$"
        assert result.address == "123 Main St"
        assert result.category == "Italian"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()
        mock_yelp_instance.get_business.assert_awaited_once_with("yelp_biz_001")

    @patch("backend.services.favorite.YelpService")
    @pytest.mark.asyncio
    async def test_add_yelp_favorite_not_found(self, mock_yelp_class, mock_db):
        """Yelp 来源收藏时商家不存在应抛出异常。"""
        from backend.core.exceptions import AppError
        from backend.services.favorite import FavoriteService

        mock_yelp_instance = mock_yelp_class.return_value
        mock_yelp_instance.get_business = AsyncMock(
            side_effect=Exception("Yelp API error")
        )

        service = FavoriteService(mock_db)
        with pytest.raises(AppError) as exc:
            await service.add_favorite("u_test", "no_such", source="yelp")
        assert exc.value.code == 404
        assert "商家不存在" in exc.value.message

    @patch("backend.services.favorite.YelpService")
    @pytest.mark.asyncio
    async def test_add_yelp_favorite_duplicate(self, mock_yelp_class, mock_db):
        """Yelp 来源重复收藏应抛出异常。"""
        from backend.core.exceptions import AppError
        from backend.services.favorite import FavoriteService

        mock_yelp_instance = mock_yelp_class.return_value
        mock_yelp_instance.get_business = AsyncMock(return_value=MagicMock())

        fav_result = MagicMock()
        fav_result.scalar_one_or_none.return_value = MagicMock()

        mock_db.execute = AsyncMock(return_value=fav_result)

        service = FavoriteService(mock_db)
        with pytest.raises(AppError) as exc:
            await service.add_favorite("u_test", "yelp_biz", source="yelp")
        assert exc.value.code == 409
        assert "已收藏" in exc.value.message


class TestRemoveFavorite:
    """测试移除收藏。"""

    @pytest.mark.asyncio
    async def test_remove_favorite_success(self, mock_db):
        """移除收藏成功。"""
        from backend.services.favorite import FavoriteService

        fav = MagicMock()
        fav.id = "fav_001"

        fav_result = MagicMock()
        fav_result.scalar_one_or_none.return_value = fav

        mock_db.execute = AsyncMock(return_value=fav_result)

        service = FavoriteService(mock_db)
        await service.remove_favorite("u_test", "biz_001")

        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_remove_favorite_not_found(self, mock_db):
        """收藏不存在应抛出异常。"""
        from backend.core.exceptions import AppError
        from backend.services.favorite import FavoriteService

        fav_result = MagicMock()
        fav_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(return_value=fav_result)

        service = FavoriteService(mock_db)
        with pytest.raises(AppError) as exc:
            await service.remove_favorite("u_test", "no_such_fav")
        assert exc.value.code == 404
        assert "收藏不存在" in exc.value.message
