"""用户路由集成测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.core.dependencies import get_current_user
from backend.database import get_db
from backend.main import app
from backend.schemas.user import UserProfileResponse


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def override_deps():
    """mock 认证 + 数据库依赖，避免连数据库。"""
    app.dependency_overrides[get_current_user] = lambda: {
        "sub": "u_abc",
        "username": "张三",
    }

    async def mock_get_db():
        return AsyncMock()

    app.dependency_overrides[get_db] = mock_get_db
    yield
    app.dependency_overrides.clear()


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
