"""Auth 请求/响应 Schema 单元测试。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserInfo,
    UserRole,
)


class TestRegisterRequest:
    """测试注册请求 Schema。"""

    def test_valid_minimal(self):
        """仅必填字段。"""
        req = RegisterRequest(username="张三", password="12345678")
        assert req.username == "张三"
        assert req.password == "12345678"
        assert req.email is None

    def test_valid_with_email(self):
        """带邮箱。"""
        req = RegisterRequest(
            username="user1", password="pass1234", email="test@example.com"
        )
        assert req.email == "test@example.com"

    def test_username_too_short(self):
        """用户名少于 2 位应报错。"""
        with pytest.raises(ValidationError):
            RegisterRequest(username="a", password="12345678")

    def test_username_too_long(self):
        """用户名超过 16 位应报错。"""
        with pytest.raises(ValidationError):
            RegisterRequest(username="a" * 17, password="12345678")

    def test_password_too_short(self):
        """密码少于 8 位应报错。"""
        with pytest.raises(ValidationError):
            RegisterRequest(username="user1", password="1234567")


class TestLoginRequest:
    """测试登录请求 Schema。"""

    def test_valid_minimal(self):
        req = LoginRequest(username="张三", password="12345678")
        assert req.username == "张三"
        assert req.password == "12345678"
        assert req.remember is False

    def test_valid_with_remember(self):
        req = LoginRequest(username="admin", password="admin123", remember=True)
        assert req.remember is True

    def test_blank_username(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="", password="12345678")


class TestTokenResponse:
    """测试 Token 响应 Schema。"""

    def test_valid(self):
        resp = TokenResponse(
            token="eyJ.eyJ.I",
            user=UserInfo(
                id="u_test",
                username="测试用户",
                role=UserRole.USER,
            ),
        )
        assert resp.token == "eyJ.eyJ.I"
        assert resp.user.username == "测试用户"
        assert resp.user.role == "user"

    def test_token_cannot_be_empty(self):
        with pytest.raises(ValidationError):
            TokenResponse(
                token="",
                user=UserInfo(id="u1", username="n", role=UserRole.USER),
            )


class TestUserInfo:
    """测试用户信息 Schema。"""

    def test_valid_minimal(self):
        user = UserInfo(id="u_abc", username="张三", role=UserRole.USER)
        assert user.id == "u_abc"
        assert user.username == "张三"
        assert user.role == "user"
        assert user.avatar == ""
        assert user.is_online is True
        assert user.email == ""
        assert user.bio == ""

    def test_valid_full(self):
        from datetime import datetime

        user = UserInfo(
            id="u_full",
            username="full_user",
            avatar="https://example.com/avatar.jpg",
            is_online=False,
            email="a@b.com",
            bio="热爱美食",
            register_time=datetime(2026, 7, 19, 14, 30, 0),
            role=UserRole.ADMIN,
        )
        assert user.avatar == "https://example.com/avatar.jpg"
        assert user.is_online is False
        assert user.role == "admin"

    def test_role_default(self):
        user = UserInfo(id="u1", username="n", role=UserRole.USER)
        assert user.role == UserRole.USER

    def test_invalid_role(self):
        """role 只能是 user 或 admin。"""
        with pytest.raises(ValidationError):
            UserInfo(id="u1", username="n", role="superadmin")  # type: ignore[arg-type]


class TestRefreshTokenRequest:
    """测试刷新 token 请求 Schema。"""

    def test_valid(self):
        req = RefreshTokenRequest(refresh_token="some.refresh.token")
        assert req.refresh_token == "some.refresh.token"

    def test_empty_token(self):
        with pytest.raises(ValidationError):
            RefreshTokenRequest(refresh_token="")
