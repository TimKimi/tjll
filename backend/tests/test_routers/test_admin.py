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
        """获取管理员信息成功。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(return_value=_ADMIN_PROFILE)
        response = client.get(
            "/api/admin/profile",
            headers={"Authorization": "Bearer admin.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["role"] == "admin"

    @patch("backend.routers.admin.AdminService")
    def test_get_admin_profile_not_admin(self, mock_service_class, client):
        """非管理员请求应返回 403。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(return_value=None)
        response = client.get(
            "/api/admin/profile",
            headers={"Authorization": "Bearer user.token"},
        )
        assert response.status_code == 403

    @patch("backend.routers.admin.AdminService")
    def test_list_users_empty(self, mock_service_class, client):
        """空用户列表。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(return_value=_ADMIN_PROFILE)
        mock_instance.list_users = AsyncMock(
            return_value=PaginatedData(
                items=[], total=0, page=1, page_size=20, total_pages=0
            )
        )
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": "Bearer admin.token"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["total"] == 0

    @patch("backend.routers.admin.AdminService")
    def test_list_users_with_items(self, mock_service_class, client):
        """用户列表包含项。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(return_value=_ADMIN_PROFILE)
        mock_instance.list_users = AsyncMock(
            return_value=PaginatedData(
                items=[
                    AdminUserItem(
                        id="u_abc",
                        username="张三",
                        email="z@e.com",
                        role="user",
                        register_time=datetime(2026, 7, 15, 14, 30, 0),
                    ),
                ],
                total=1,
                page=1,
                page_size=20,
                total_pages=1,
            )
        )
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": "Bearer admin.token"},
        )
        assert response.json()["data"]["items"][0]["username"] == "张三"

    @patch("backend.routers.admin.AdminService")
    def test_list_users_requires_auth(self, mock_service_class, client):
        """未认证请求应返回 401。"""
        from backend.core.dependencies import get_current_user
        from backend.main import app

        orig = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            __import__("fastapi").HTTPException(
                status_code=401, detail="未授权，请先登录"
            )
        )
        response = client.get("/api/admin/users")
        assert response.status_code == 401
        if orig is not None:
            app.dependency_overrides[get_current_user] = orig
        else:
            del app.dependency_overrides[get_current_user]

    @patch("backend.routers.admin.AdminService")
    def test_update_role_success(self, mock_service_class, client):
        """修改用户角色成功。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(return_value=_ADMIN_PROFILE)
        mock_instance.change_role = AsyncMock(
            return_value=AdminUserItem(id="u_target", username="target", role="admin")
        )
        response = client.put(
            "/api/admin/users/u_target/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer admin.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["role"] == "admin"

    @patch("backend.routers.admin.AdminService")
    def test_update_role_not_admin(self, mock_service_class, client):
        """非管理员修改角色应返回 403。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(return_value=None)
        response = client.put(
            "/api/admin/users/u_target/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer user.token"},
        )
        assert response.status_code == 403

    @patch("backend.routers.admin.AdminService")
    def test_delete_user_success(self, mock_service_class, client):
        """删除用户成功。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(return_value=_ADMIN_PROFILE)
        mock_instance.delete_user = AsyncMock(return_value=None)
        response = client.delete(
            "/api/admin/users/u_target",
            headers={"Authorization": "Bearer admin.token"},
        )
        assert response.status_code == 200

    @patch("backend.routers.admin.AdminService")
    def test_delete_user_not_admin(self, mock_service_class, client):
        """非管理员删除用户应返回 403。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_admin_profile = AsyncMock(return_value=None)
        response = client.delete(
            "/api/admin/users/u_target",
            headers={"Authorization": "Bearer user.token"},
        )
        assert response.status_code == 403
