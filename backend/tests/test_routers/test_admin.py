"""Admin 路由集成测试。"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

from backend.schemas.admin import AdminProfileResponse, AdminUserItem
from backend.schemas.common import PaginatedData


_ADMIN_PROFILE = AdminProfileResponse(
    id="u_admin",
    username="管理员",
    avatar="https://example.com/admin_avatar.jpg",
    role="admin",
)


class TestAdminRoutes:
    """测试 Admin 路由端点。"""

    @patch("backend.routers.admin.AdminService")
    def test_get_admin_profile_success(self, mock_service_class, client):
        """获取管理员信息成功应返回 200 + 管理员信息。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(
            return_value=AdminProfileResponse(
                id="u_admin",
                username="管理员",
                avatar="https://example.com/admin_avatar.jpg",
                role="admin",
            )
        )
        response = client.get(
            "/api/admin/profile",
            headers={"Authorization": "Bearer admin.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == "u_admin"
        assert data["data"]["username"] == "管理员"
        assert data["data"]["role"] == "admin"

    @patch("backend.routers.admin.AdminService")
    def test_get_admin_profile_not_admin(self, mock_service_class, client):
        """非管理员请求应返回 403。"""
        from fastapi import HTTPException

        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(
            side_effect=HTTPException(status_code=403, detail="权限不足")
        )
        response = client.get(
            "/api/admin/profile",
            headers={"Authorization": "Bearer user.token"},
        )
        assert response.status_code == 403

    @patch("backend.routers.admin.AdminService")
    def test_list_users_empty(self, mock_service_class, client):
        """空用户列表应返回空列表。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(return_value=_ADMIN_PROFILE)
        mock_instance.list_users = AsyncMock(
            return_value=PaginatedData(
                items=[],
                total=0,
                page=1,
                page_size=20,
                total_pages=0,
            )
        )
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": "Bearer admin.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    @patch("backend.routers.admin.AdminService")
    def test_list_users_with_items(self, mock_service_class, client):
        """用户列表应返回用户项。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(return_value=_ADMIN_PROFILE)
        mock_instance.list_users = AsyncMock(
            return_value=PaginatedData(
                items=[
                    AdminUserItem(
                        id="u_abc123",
                        username="张三",
                        email="zhangsan@example.com",
                        bio="热爱美食，分享生活",
                        avatar="",
                        is_online=True,
                        register_time=datetime(2026, 7, 15, 14, 30, 0),
                        role="user",
                    ),
                    AdminUserItem(
                        id="u_def456",
                        username="李四",
                        email="lisi@example.com",
                        bio="",
                        avatar="",
                        is_online=False,
                        register_time=datetime(2026, 7, 16, 10, 0, 0),
                        role="user",
                    ),
                ],
                total=2,
                page=1,
                page_size=20,
                total_pages=1,
            )
        )
        response = client.get(
            "/api/admin/users?page=1&page_size=20",
            headers={"Authorization": "Bearer admin.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["items"]) == 2
        assert data["data"]["items"][0]["username"] == "张三"
        assert data["data"]["items"][0]["role"] == "user"
        assert data["data"]["items"][1]["username"] == "李四"
        assert data["data"]["total"] == 2

    @patch("backend.routers.admin.AdminService")
    def test_list_users_with_keyword(self, mock_service_class, client):
        """带关键词搜索的用户列表。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(return_value=_ADMIN_PROFILE)
        mock_instance.list_users = AsyncMock(
            return_value=PaginatedData(
                items=[
                    AdminUserItem(
                        id="u_abc123",
                        username="张三",
                        email="zhangsan@example.com",
                        bio="热爱美食",
                        avatar="",
                        is_online=True,
                        register_time=datetime(2026, 7, 15, 14, 30, 0),
                        role="user",
                    ),
                ],
                total=1,
                page=1,
                page_size=20,
                total_pages=1,
            )
        )
        response = client.get(
            "/api/admin/users?keyword=张三",
            headers={"Authorization": "Bearer admin.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["username"] == "张三"

    @patch("backend.routers.admin.AdminService")
    def test_list_users_requires_auth(self, mock_service_class, client):
        """未认证请求应返回 401。"""
        from backend.core.dependencies import get_current_user
        from backend.main import app

        original_override = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            __import__("fastapi").HTTPException(
                status_code=401, detail="未授权，请先登录"
            )
        )

        response = client.get("/api/admin/users")
        assert response.status_code == 401

        if original_override is not None:
            app.dependency_overrides[get_current_user] = original_override
        else:
            del app.dependency_overrides[get_current_user]
