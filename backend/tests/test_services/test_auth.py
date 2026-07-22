"""Auth 服务层单元测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.auth import LoginRequest, RegisterRequest, UserRole


@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


class TestRegister:
    """测试用户注册。"""

    @pytest.mark.asyncio
    async def test_register_creates_user(self, mock_db):
        """注册成功应返回用户信息和 token。"""
        from backend.services.auth import AuthService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # 用户名不重复
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        req = RegisterRequest(
            username="新用户", password="pass1234", email="new@example.com"
        )
        result = await service.register(req)

        assert result.user.username == "新用户"
        assert result.user.role == UserRole.USER
        assert result.token != ""
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, mock_db):
        """重复用户名应抛出异常。"""
        from backend.core.exceptions import AppError
        from backend.services.auth import AuthService

        existing_user = MagicMock()
        existing_user.username = "新用户"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        req = RegisterRequest(
            username="新用户", password="pass1234", email="dup@example.com"
        )
        with pytest.raises(AppError) as exc:
            await service.register(req)
        assert "已存在" in str(exc.value)

    @pytest.mark.asyncio
    async def test_register_password_is_hashed(self, mock_db):
        """注册时密码应被哈希存储。"""
        from backend.services.auth import AuthService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        req = RegisterRequest(
            username="user1", password="plain_password", email="pw@example.com"
        )
        await service.register(req)

        added_user = mock_db.add.call_args[0][0]
        assert added_user.password_hash != "plain_password"
        assert added_user.password_hash.startswith("$2b$")

    @pytest.mark.asyncio
    async def test_register_with_email(self, mock_db):
        """注册时可附带邮箱。"""
        from backend.services.auth import AuthService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        req = RegisterRequest(
            username="user_email", password="pass1234", email="user@example.com"
        )
        await service.register(req)

        added_user = mock_db.add.call_args[0][0]
        assert added_user.email == "user@example.com"


class TestLogin:
    """测试用户登录。"""

    @pytest.mark.asyncio
    async def test_login_success(self, mock_db):
        """正确的用户名密码应返回 token。"""
        from backend.core.security import hash_password
        from backend.services.auth import AuthService

        mock_user = MagicMock()
        mock_user.id = "u_abc123"
        mock_user.username = "test_user"
        mock_user.password_hash = hash_password("correct_pw")
        mock_user.avatar = ""
        mock_user.is_online = False
        mock_user.email = ""
        mock_user.bio = ""

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        req = LoginRequest(username="test_user", password="correct_pw")
        result = await service.login(req)

        assert result.user.username == "test_user"
        assert result.token != ""

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, mock_db):
        """密码错误应抛出异常。"""
        from backend.core.exceptions import AppError
        from backend.core.security import hash_password
        from backend.services.auth import AuthService

        mock_user = MagicMock()
        mock_user.id = "u_abc"
        mock_user.password_hash = hash_password("real_pw")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        req = LoginRequest(username="test_user", password="wrong_pw")
        with pytest.raises(AppError) as exc:
            await service.login(req)
        assert "密码错误" in str(exc.value)

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, mock_db):
        """用户不存在应抛出异常。"""
        from backend.core.exceptions import AppError
        from backend.services.auth import AuthService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        req = LoginRequest(username="no_one", password="pass1234")
        with pytest.raises(AppError) as exc:
            await service.login(req)
        assert "用户名或密码错误" in str(exc.value)
        assert exc.value.code == 401

    @pytest.mark.asyncio
    async def test_login_updates_is_online(self, mock_db):
        """登录成功后应标记用户在线。"""
        from backend.core.security import hash_password
        from backend.services.auth import AuthService

        mock_user = MagicMock()
        mock_user.id = "u_online"
        mock_user.username = "test_user"
        mock_user.password_hash = hash_password("pw")
        mock_user.avatar = ""
        mock_user.is_online = False
        mock_user.email = ""
        mock_user.bio = ""
        mock_user.role = "user"
        mock_user.register_time = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        req = LoginRequest(username="u", password="pw")
        await service.login(req)

        assert mock_user.is_online is True
        mock_db.commit.assert_awaited_once()


class TestLogout:
    """测试退出登录。"""

    @pytest.mark.asyncio
    async def test_logout_marks_user_offline(self, mock_db):
        """退出应标记用户离线。"""
        from backend.services.auth import AuthService

        mock_user = MagicMock()
        mock_user.id = "u_abc"
        mock_user.is_online = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        await service.logout("u_abc")

        assert mock_user.is_online is False
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_logout_user_not_found(self, mock_db):
        """不存在的用户退出应不报错。"""
        from backend.services.auth import AuthService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        await service.logout("no_such_user")
        # should not raise


class TestForgotPassword:
    """测试密码找回。"""

    @pytest.mark.asyncio
    async def test_forgot_password_existing_user(self, mock_db):
        """存在的邮箱应发送重置邮件（不抛出异常）。"""
        from backend.services.auth import AuthService

        mock_user = MagicMock()
        mock_user.id = "u_abc"
        mock_user.username = "test_user"
        mock_user.email = "user@example.com"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        await service.forgot_password("user@example.com")
        assert mock_user.reset_token is not None
        assert mock_user.reset_token_exp is not None
        mock_db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_email(self, mock_db):
        """不存在的邮箱不应抛出异常（防止枚举）。"""
        from backend.services.auth import AuthService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        await service.forgot_password("no@one.com")
        # should not raise


class TestResetPassword:
    """测试密码重置（24 位 hex 密钥，邮箱签名内置）。"""

    @pytest.mark.asyncio
    async def test_reset_password_success(self, mock_db):
        """有效的密钥 + 匹配的哈希 → 重置成功。"""
        from datetime import datetime, timedelta, timezone
        from backend.services.auth import AuthService, _hash_token

        # 24 位 hex 密钥（服务端会自动去格式化、小写化）
        raw_token = "abcd1234ef567890abcd1234"
        mock_user = MagicMock()
        mock_user.id = "u_abc"
        mock_user.reset_token = _hash_token(raw_token)
        mock_user.reset_token_exp = datetime.now(timezone.utc).replace(
            tzinfo=None
        ) + timedelta(hours=1)
        mock_user.password_hash = "old_hash"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        await service.reset_password(raw_token, "new_password_123")

        assert mock_user.password_hash != "old_hash"
        assert mock_user.reset_token is None
        assert mock_user.reset_token_exp is None
        mock_db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_reset_password_with_formatting(self, mock_db):
        """带短横线和大写的格式化密钥也应能正常解析。"""
        from datetime import datetime, timedelta, timezone
        from backend.services.auth import AuthService, _hash_token

        clean_token = "abcd1234ef567890abcd1234"
        # 用户可能输入 ABCD-1234-EF56-7890-ABCD-1234 格式
        formatted_input = "ABCD-1234-EF56-7890-ABCD-1234"
        mock_user = MagicMock()
        mock_user.id = "u_abc"
        mock_user.reset_token = _hash_token(clean_token)
        mock_user.reset_token_exp = datetime.now(timezone.utc).replace(
            tzinfo=None
        ) + timedelta(hours=1)
        mock_user.password_hash = "old_hash"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        await service.reset_password(formatted_input, "new_password_123")

        assert mock_user.password_hash != "old_hash"
        mock_db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, mock_db):
        """数据库中不存在的密钥应拒绝。"""
        from backend.core.exceptions import AppError
        from backend.services.auth import AuthService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        with pytest.raises(AppError, match="密钥无效"):
            await service.reset_password("ffffffffffffffffffffffff", "new_pw")

    @pytest.mark.asyncio
    async def test_reset_password_expired_token(self, mock_db):
        """过期的密钥应拒绝并清除。"""
        from datetime import datetime, timedelta, timezone
        from backend.core.exceptions import AppError
        from backend.services.auth import AuthService, _hash_token

        raw_token = "deadbeef12345678deadbeef"
        mock_user = MagicMock()
        mock_user.id = "u_expired"
        mock_user.reset_token = _hash_token(raw_token)
        mock_user.reset_token_exp = datetime.now(timezone.utc).replace(
            tzinfo=None
        ) - timedelta(hours=1)  # 已过期
        mock_user.password_hash = "old_hash"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        service = AuthService(mock_db)
        with pytest.raises(AppError, match="密钥已过期"):
            await service.reset_password(raw_token, "new_pw")
        # 过期后应清除 token
        assert mock_user.reset_token is None
        assert mock_user.reset_token_exp is None
