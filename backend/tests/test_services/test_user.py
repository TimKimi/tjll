"""User 服务层单元测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.user import UpdateProfileRequest


@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_user():
    user = MagicMock()
    user.id = "u_abc123"
    user.username = "张三"
    user.email = "zhangsan@example.com"
    user.bio = "这个人很懒，什么都没写~"
    user.avatar = ""
    user.is_online = True
    user.register_time = None
    return user


class TestGetProfile:
    """测试获取用户信息。"""

    @pytest.mark.asyncio
    async def test_get_profile_found(self, mock_db, sample_user):
        """获取存在的用户应返回信息。"""
        from backend.services.user import UserService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result

        service = UserService(mock_db)
        result = await service.get_profile("u_abc123")

        assert result is not None
        assert result.id == "u_abc123"
        assert result.username == "张三"
        assert result.email == "zhangsan@example.com"

    @pytest.mark.asyncio
    async def test_get_profile_not_found(self, mock_db):
        """不存在的用户应返回 None。"""
        from backend.services.user import UserService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = UserService(mock_db)
        result = await service.get_profile("no_such_user")
        assert result is None


class TestUpdateProfile:
    """测试更新用户信息。"""

    @pytest.mark.asyncio
    async def test_update_username(self, mock_db, sample_user):
        """更新用户名。"""
        from backend.services.user import UserService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result

        service = UserService(mock_db)
        req = UpdateProfileRequest(username="新名字")
        result = await service.update_profile("u_abc123", req)
        assert result is not None
        assert result.username == "新名字"
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_email(self, mock_db, sample_user):
        """更新邮箱。"""
        from backend.services.user import UserService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result

        service = UserService(mock_db)
        req = UpdateProfileRequest(email="new@example.com")
        result = await service.update_profile("u_abc123", req)
        assert result is not None
        assert result.email == "new@example.com"

    @pytest.mark.asyncio
    async def test_update_bio(self, mock_db, sample_user):
        """更新个性签名。"""
        from backend.services.user import UserService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result

        service = UserService(mock_db)
        req = UpdateProfileRequest(bio="热爱美食，分享生活")
        result = await service.update_profile("u_abc123", req)
        assert result is not None
        assert result.bio == "热爱美食，分享生活"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, mock_db):
        """不存在的用户应返回 None。"""
        from backend.services.user import UserService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = UserService(mock_db)
        req = UpdateProfileRequest(username="新名字")
        result = await service.update_profile("no_such_user", req)
        assert result is None
        mock_db.commit.assert_not_called()
