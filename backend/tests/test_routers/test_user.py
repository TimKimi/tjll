"""用户路由集成测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from backend.schemas.user import UserProfileResponse


class TestUserRoutes:
    """测试用户路由端点。"""

    @patch("backend.routers.user.UserService")
    def test_get_profile(self, mock_service_class, client):
        """获取用户信息。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_profile = AsyncMock(
            return_value=UserProfileResponse(id="u_abc", username="张三"),
        )
        response = client.get(
            "/api/user/profile",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["username"] == "张三"

    @patch("backend.routers.user.UserService")
    def test_get_profile_not_found(self, mock_service_class, client):
        """用户不存在。"""
        mock_instance = mock_service_class.return_value
        mock_instance.get_profile = AsyncMock(return_value=None)
        response = client.get(
            "/api/user/profile",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 404

    @patch("backend.routers.user.UserService")
    def test_update_profile(self, mock_service_class, client):
        """更新用户信息。"""
        mock_instance = mock_service_class.return_value
        mock_instance.update_profile = AsyncMock(
            return_value=UserProfileResponse(
                id="u_abc", username="新名字", email="new@example.com"
            ),
        )
        response = client.put(
            "/api/user/profile",
            json={"username": "新名字", "email": "new@example.com"},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["username"] == "新名字"
