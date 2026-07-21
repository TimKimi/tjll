"""收藏路由集成测试。"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

from backend.schemas.common import PaginatedData
from backend.schemas.favorite import FavoriteItem


class TestFavoriteRoutes:
    """测试收藏路由端点。"""

    @patch("backend.routers.favorite.FavoriteService")
    def test_list_favorites_empty(self, mock_service_class, client):
        """空收藏列表应返回空列表。"""
        mock_instance = mock_service_class.return_value
        mock_instance.list_favorites = AsyncMock(
            return_value=PaginatedData(
                items=[],
                total=0,
                page=1,
                page_size=20,
                total_pages=0,
            )
        )
        response = client.get(
            "/api/favorites",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    @patch("backend.routers.favorite.FavoriteService")
    def test_list_favorites_with_items(self, mock_service_class, client):
        """收藏列表应返回收藏项。"""
        mock_instance = mock_service_class.return_value
        mock_instance.list_favorites = AsyncMock(
            return_value=PaginatedData(
                items=[
                    FavoriteItem(
                        id="fav_001",
                        shop_id="biz_001",
                        name="蜀九香火锅",
                        image_url="https://example.com/shop1.jpg",
                        rating=4.8,
                        price="$$",
                        address="锦江区春熙路88号",
                        category="火锅",
                        created_at=datetime(2026, 7, 19, 15, 0, 0),
                    ),
                ],
                total=1,
                page=1,
                page_size=20,
                total_pages=1,
            )
        )
        response = client.get(
            "/api/favorites?page=1&page_size=20",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["shop_id"] == "biz_001"
        assert data["data"]["items"][0]["name"] == "蜀九香火锅"
        assert data["data"]["items"][0]["category"] == "火锅"
        assert data["data"]["total"] == 1

    @patch("backend.routers.favorite.FavoriteService")
    def test_list_favorites_requires_auth(self, mock_service_class, client):
        """未认证请求应返回 401。"""
        # 清除自动 mock 的认证依赖，模拟无 token 请求
        from backend.core.dependencies import get_current_user
        from backend.main import app

        original_override = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            __import__("fastapi").HTTPException(
                status_code=401, detail="未授权，请先登录"
            )
        )

        response = client.get("/api/favorites")
        assert response.status_code == 401

        # 恢复
        if original_override is not None:
            app.dependency_overrides[get_current_user] = original_override
        else:
            del app.dependency_overrides[get_current_user]

    @patch("backend.routers.favorite.FavoriteService")
    def test_add_favorite_success(self, mock_service_class, client):
        """添加收藏成功。"""
        mock_instance = mock_service_class.return_value
        mock_instance.add_favorite = AsyncMock(
            return_value=FavoriteItem(
                id="fav_001",
                shop_id="biz_001",
                name="蜀九香火锅",
                image_url="https://example.com/shop1.jpg",
                rating=4.8,
                price="$$",
                address="锦江区春熙路88号",
                category="火锅",
                created_at=datetime(2026, 7, 19, 15, 0, 0),
            )
        )
        response = client.post(
            "/api/favorites",
            json={"shop_id": "biz_001"},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["shop_id"] == "biz_001"
        assert data["message"] == "收藏成功"

    @patch("backend.routers.favorite.FavoriteService")
    def test_add_favorite_duplicate(self, mock_service_class, client):
        """重复收藏应返回 409。"""
        from backend.core.exceptions import AppError

        mock_instance = mock_service_class.return_value
        mock_instance.add_favorite = AsyncMock(
            side_effect=AppError("已收藏该商家", code=409)
        )
        response = client.post(
            "/api/favorites",
            json={"shop_id": "biz_001"},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 409

    @patch("backend.routers.favorite.FavoriteService")
    def test_add_favorite_shop_not_found(self, mock_service_class, client):
        """商家不存在应返回 404。"""
        from backend.core.exceptions import AppError

        mock_instance = mock_service_class.return_value
        mock_instance.add_favorite = AsyncMock(
            side_effect=AppError("商家不存在", code=404)
        )
        response = client.post(
            "/api/favorites",
            json={"shop_id": "nonexistent"},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 404

    @patch("backend.routers.favorite.FavoriteService")
    def test_remove_favorite_success(self, mock_service_class, client):
        """移除收藏成功。"""
        mock_instance = mock_service_class.return_value
        mock_instance.remove_favorite = AsyncMock(return_value=None)
        response = client.delete(
            "/api/favorites/biz_001",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "移除收藏成功"

    @patch("backend.routers.favorite.FavoriteService")
    def test_remove_favorite_not_found(self, mock_service_class, client):
        """收藏不存在应返回 404。"""
        from backend.core.exceptions import AppError

        mock_instance = mock_service_class.return_value
        mock_instance.remove_favorite = AsyncMock(
            side_effect=AppError("收藏不存在", code=404)
        )
        response = client.delete(
            "/api/favorites/biz_not_found",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 404
