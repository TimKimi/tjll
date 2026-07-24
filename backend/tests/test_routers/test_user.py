"""用户路由集成测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.database import get_db
from backend.main import app


class TestUserRoutes:
    """测试用户路由端点。"""

    # ── 辅助方法 ──────────────────────────────────────────

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

    def _mock_setting(self, **kwargs) -> MagicMock:
        """创建模拟的 UserSetting 实例。"""
        s = MagicMock()
        defaults = {
            "id": "s_abc",
            "user_id": "u_test",
            "insight_create": False,
            "insight_use": False,
            "created_at": None,
            "updated_at": None,
        }
        for k, v in {**defaults, **kwargs}.items():
            setattr(s, k, v)
        return s

    def _set_user_found(self, user: MagicMock | None) -> None:
        """配置 mock_db 返回指定用户。"""
        mock_db = app.dependency_overrides[get_db]()
        mock_db.execute.return_value.scalar_one_or_none.return_value = user

    def _set_setting_found(self, setting: MagicMock | None) -> None:
        """配置 mock_db 返回指定设置记录。"""
        mock_db = app.dependency_overrides[get_db]()
        mock_db.execute.return_value.scalar_one_or_none.return_value = setting

    # ── Profile ──────────────────────────────────────────

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

    # ── Settings ─────────────────────────────────────────

    def test_get_settings_defaults(self, client):
        """设置无记录时返回默认值。"""
        self._set_setting_found(None)
        response = client.get(
            "/api/user/settings",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["insight_create"] is False
        assert data["data"]["insight_use"] is False

    def test_get_settings(self, client):
        """获取已有设置。"""
        self._set_setting_found(self._mock_setting(insight_create=True))
        response = client.get(
            "/api/user/settings",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["insight_create"] is True

    def test_update_settings(self, client):
        """更新设置（已有记录）。"""
        self._set_setting_found(self._mock_setting())
        response = client.put(
            "/api/user/settings",
            json={"insight_create": True},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_update_settings_create_new(self, client):
        """更新设置（无记录→新建）。"""
        self._set_setting_found(None)
        response = client.put(
            "/api/user/settings",
            json={"insight_use": True},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_reset_settings(self, client):
        """重置设置为默认值。"""
        self._set_setting_found(self._mock_setting(insight_create=True))
        response = client.post(
            "/api/user/settings/reset",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "已重置为默认值"

    def test_reset_settings_create_new(self, client):
        """重置设置（无记录→新建）。"""
        self._set_setting_found(None)
        response = client.post(
            "/api/user/settings/reset",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    # ── 注销账号 ─────────────────────────────────────────

    def test_delete_account(self, client):
        """注销账号成功。"""
        self._set_user_found(self._mock_user())
        response = client.delete(
            "/api/user/account",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "已删除"

    def test_delete_account_not_found(self, client):
        """用户不存在时返回 404。"""
        self._set_user_found(None)
        response = client.delete(
            "/api/user/account",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 404

    def test_delete_account_requires_auth(self, client):
        """未认证请求返回 401。"""
        from backend.core.dependencies import get_current_user

        original = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            __import__("fastapi").HTTPException(status_code=401, detail="未授权")
        )
        try:
            response = client.delete("/api/user/account")
            assert response.status_code == 401
        finally:
            if original is not None:
                app.dependency_overrides[get_current_user] = original
            else:
                del app.dependency_overrides[get_current_user]


class TestCleanupUserResources:
    """测试 _cleanup_user_resources 文件清理逻辑。"""

    @pytest.mark.asyncio
    async def _call(self, **user_kw) -> None:
        """调用 _cleanup_user_resources 并传入 mock 用户。"""
        from unittest.mock import AsyncMock
        from backend.routers.user import _cleanup_user_resources

        user = MagicMock()
        defaults = {
            "id": "u_test",
            "username": "测试用户",
            "avatar": "/static/avatars/test.jpg",
        }
        for k, v in {**defaults, **user_kw}.items():
            setattr(user, k, v)
        await _cleanup_user_resources(user, AsyncMock())

    @pytest.mark.asyncio
    async def test_avatar_file_deleted(self):
        """用户有头像时删除头像文件。"""
        from unittest.mock import patch

        with patch("backend.routers.user.Path.exists", return_value=True):
            with patch("backend.routers.user.Path.unlink") as mock_unlink:
                await self._call()
                mock_unlink.assert_called_once()

    @pytest.mark.asyncio
    async def test_avatar_file_not_exists(self):
        """头像文件已不存在时不报错。"""
        from unittest.mock import patch

        with patch("backend.routers.user.Path.exists", return_value=False):
            with patch("backend.routers.user.Path.unlink") as mock_unlink:
                await self._call()
                mock_unlink.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_avatar_skips_file_deletion(self):
        """用户无头像时不执行文件删除（但附件目录仍会处理）。"""
        from unittest.mock import patch

        with patch("backend.routers.user.shutil.rmtree"):
            with patch("backend.routers.user.Path.unlink") as mock_unlink:
                await self._call(avatar="")
                mock_unlink.assert_not_called()
                # avatar 为空时应该不会尝试删头像文件
                # 但附件目录仍会处理（因为 username 有值）

    @pytest.mark.asyncio
    async def test_user_file_dir_deleted(self):
        """有用户名时删除附件目录。"""
        from unittest.mock import patch

        with patch("backend.routers.user.Path.exists", return_value=True):
            with patch("backend.routers.user.shutil.rmtree") as mock_rmtree:
                await self._call()
                mock_rmtree.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_username_skips_dir_deletion(self):
        """用户无用户名时跳过附件目录删除（但头像仍会处理）。"""
        from unittest.mock import patch

        with patch("backend.routers.user.shutil.rmtree") as mock_rmtree:
            with patch("backend.routers.user.Path.unlink"):
                await self._call(username="")
                mock_rmtree.assert_not_called()
                # username 为空时应该不会尝试删附件目录
                # 但头像仍会处理（因为 avatar 有值）

    @pytest.mark.asyncio
    async def test_oserror_logged_not_raised(self):
        """文件删除失败只打 warning，不抛异常。"""
        from unittest.mock import patch

        with patch("backend.routers.user.Path.exists", return_value=True):
            with patch(
                "backend.routers.user.Path.unlink",
                side_effect=OSError("permission denied"),
            ):
                await self._call()  # 不应抛异常


class TestUserInsightRoutes:
    """测试用户画像路由。"""

    @patch("backend.routers.user.get_user_insight")
    def test_get_insight(self, mock_get, client):
        """获取用户画像成功。"""
        mock_get.return_value = {"喜好": "川菜", "口味": "偏辣"}
        response = client.get(
            "/api/user/insight",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["喜好"] == "川菜"

    @patch("backend.routers.user.update_user_insight_attrs")
    def test_update_insight(self, mock_update, client):
        """更新用户画像成功。"""
        mock_update.return_value = True
        response = client.put(
            "/api/user/insight",
            json={"喜好": "粤菜"},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "画像已更新"

    @patch("backend.routers.user.delete_user_insight")
    def test_delete_insight(self, mock_delete, client):
        """删除用户画像成功。"""
        mock_delete.return_value = True
        response = client.delete(
            "/api/user/insight",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "画像已删除"

    @patch("backend.routers.user.delete_all_insights")
    def test_delete_all_insights(self, mock_delete, client):
        """删除所有画像成功。"""
        mock_delete.return_value = True
        response = client.delete(
            "/api/user/insights",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "所有画像已删除"
