"""用户路由集成测试。"""

from __future__ import annotations

from unittest.mock import MagicMock

from backend.database import get_db
from backend.main import app


class TestUserRoutes:
    """测试用户路由端点。"""

    def _mock_user(self, **kwargs) -> MagicMock:
        """创建模拟的 AppUser 实例。"""
        user = MagicMock()
        defaults = {
            "id": "u_abc",
            "username": "张三",
            "avatar": "",
            "is_online": True,
            "email": "",
            "bio": "",
            "register_time": None,
        }
        for k, v in {**defaults, **kwargs}.items():
            setattr(user, k, v)
        return user

    def _set_user_found(self, user: MagicMock | None) -> None:
        """配置 mock_db 返回指定用户。"""
        mock_db = app.dependency_overrides[get_db]()
        mock_db.execute.return_value.scalar_one_or_none.return_value = user

    def test_get_profile(self, client):
        """获取用户信息。"""
        self._set_user_found(self._mock_user(username="张三"))
        response = client.get(
            "/api/user/profile",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["username"] == "张三"

    def test_get_profile_not_found(self, client):
        """用户不存在。"""
        self._set_user_found(None)
        response = client.get(
            "/api/user/profile",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 404

    def test_update_profile(self, client):
        """更新用户信息。"""
        self._set_user_found(self._mock_user(username="张三"))
        response = client.put(
            "/api/user/profile",
            json={"username": "新名字", "email": "new@example.com"},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["username"] == "新名字"
