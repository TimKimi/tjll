"""Admin 服务层单元测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    return db


class TestChangeRole:
    """测试修改用户角色。"""

    @pytest.mark.asyncio
    async def test_change_role_success(self, mock_db):
        """管理员可将用户角色从 user 改为 admin。"""
        from backend.services.admin import AdminService

        target_user = MagicMock()
        target_user.id = "u_target"
        target_user.username = "target"
        target_user.role = "user"
        target_user.email = ""
        target_user.avatar = ""
        target_user.bio = ""
        target_user.is_online = False
        target_user.register_time = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = target_user
        mock_db.execute.return_value = mock_result

        service = AdminService(mock_db)
        result = await service.change_role("u_admin", "u_target", "admin")

        assert target_user.role == "admin"
        assert result.role == "admin"
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_change_role_self_not_allowed(self, mock_db):
        """管理员不能修改自己的角色。"""
        from backend.core.exceptions import AppError
        from backend.services.admin import AdminService

        service = AdminService(mock_db)
        with pytest.raises(AppError, match="不能修改自己的角色"):
            await service.change_role("u_admin", "u_admin", "admin")

    @pytest.mark.asyncio
    async def test_change_role_user_not_found(self, mock_db):
        """不存在的用户应抛出异常。"""
        from backend.core.exceptions import AppError
        from backend.services.admin import AdminService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AdminService(mock_db)
        with pytest.raises(AppError, match="用户不存在"):
            await service.change_role("u_admin", "u_no_such", "admin")


class TestDeleteUser:
    """测试删除用户。"""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, mock_db):
        """管理员可删除其他用户。"""
        from backend.services.admin import AdminService

        target_user = MagicMock()
        target_user.id = "u_target"
        target_user.username = "target"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = target_user
        mock_db.execute.return_value = mock_result

        service = AdminService(mock_db)
        await service.delete_user("u_admin", "u_target")

        mock_db.delete.assert_called_once_with(target_user)
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_user_self_not_allowed(self, mock_db):
        """管理员不能删除自己的账号。"""
        from backend.core.exceptions import AppError
        from backend.services.admin import AdminService

        service = AdminService(mock_db)
        with pytest.raises(AppError, match="不能删除自己的账号"):
            await service.delete_user("u_admin", "u_admin")

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, mock_db):
        """不存在的用户应抛出异常。"""
        from backend.core.exceptions import AppError
        from backend.services.admin import AdminService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AdminService(mock_db)
        with pytest.raises(AppError, match="用户不存在"):
            await service.delete_user("u_admin", "u_no_such")
