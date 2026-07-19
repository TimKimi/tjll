"""认证路由集成测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from backend.schemas.auth import TokenResponse, UserInfo, UserRole


class TestAuthRoutes:
    """测试认证路由端点。"""

    @patch("backend.routers.auth.AuthService")
    def test_register_success(self, mock_service_class, client):
        """注册成功应返回 201 + token。"""
        mock_instance = mock_service_class.return_value
        mock_instance.register = AsyncMock(
            return_value=TokenResponse(
                token="eyJ.test.token",
                user=UserInfo(id="u_new", username="新用户", role=UserRole.USER),
            )
        )
        response = client.post(
            "/api/auth/register",
            json={
                "username": "新用户",
                "password": "pass1234",
                "email": "user@example.com",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["token"] == "eyJ.test.token"
        assert data["data"]["user"]["username"] == "新用户"

    @patch("backend.routers.auth.AuthService")
    def test_register_duplicate(self, mock_service_class, client):
        """重复用户名应返回 400。"""
        from backend.core.exceptions import AppError

        mock_instance = mock_service_class.return_value
        mock_instance.register = AsyncMock(
            side_effect=AppError("用户名已存在", code=400)
        )
        response = client.post(
            "/api/auth/register",
            json={
                "username": "existing",
                "password": "pass1234",
                "email": "dup@example.com",
            },
        )
        assert response.status_code == 400

    @patch("backend.routers.auth.AuthService")
    def test_login_success(self, mock_service_class, client):
        """登录成功应返回 200 + token。"""
        mock_instance = mock_service_class.return_value
        mock_instance.login = AsyncMock(
            return_value=TokenResponse(
                token="eyJ.login.token",
                user=UserInfo(id="u_1", username="张三", role=UserRole.USER),
            )
        )
        response = client.post(
            "/api/auth/login",
            json={"username": "张三", "password": "pass1234"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["token"] == "eyJ.login.token"

    @patch("backend.routers.auth.AuthService")
    def test_login_wrong_password(self, mock_service_class, client):
        """密码错误应返回 401。"""
        from backend.core.exceptions import AppError

        mock_instance = mock_service_class.return_value
        mock_instance.login = AsyncMock(side_effect=AppError("密码错误", code=401))
        response = client.post(
            "/api/auth/login",
            json={"username": "张三", "password": "wrong"},
        )
        assert response.status_code == 401

    @patch("backend.routers.auth.AuthService")
    def test_logout_success(self, mock_service_class, client):
        """退出登录应返回 200。"""
        mock_instance = mock_service_class.return_value
        mock_instance.logout = AsyncMock(return_value=None)
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer test.token.here"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "退出成功"

    @patch("backend.routers.auth.AuthService")
    def test_admin_login_success(self, mock_service_class, client):
        """管理员登录。"""
        mock_instance = mock_service_class.return_value
        mock_instance.login = AsyncMock(
            return_value=TokenResponse(
                token="eyJ.admin.token",
                user=UserInfo(id="u_admin", username="管理员", role=UserRole.ADMIN),
            )
        )
        response = client.post(
            "/api/auth/admin/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["user"]["role"] == "admin"
