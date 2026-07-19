"""User Profile 请求/响应 Schema 单元测试。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.schemas.user import UpdateProfileRequest, UserProfileResponse


class TestUserProfileResponse:
    """测试用户信息响应 Schema。"""

    def test_valid_minimal(self):
        resp = UserProfileResponse(
            id="u_abc",
            username="张三",
        )
        assert resp.id == "u_abc"
        assert resp.username == "张三"
        assert resp.avatar == ""
        assert resp.is_online is True
        assert resp.email == ""
        assert resp.bio == ""

    def test_valid_full(self):
        from datetime import datetime

        resp = UserProfileResponse(
            id="u_full",
            username="full_user",
            avatar="https://example.com/avatar.jpg",
            is_online=False,
            email="a@b.com",
            bio="热爱美食",
            register_time=datetime(2026, 7, 19, 14, 30, 0),
        )
        assert resp.avatar == "https://example.com/avatar.jpg"
        assert resp.is_online is False


class TestUpdateProfileRequest:
    """测试更新用户信息请求 Schema。"""

    def test_all_fields_optional(self):
        """全部字段选填。"""
        req = UpdateProfileRequest()
        assert req.username is None
        assert req.email is None
        assert req.bio is None

    def test_partial_update(self):
        """只更新部分字段。"""
        req = UpdateProfileRequest(username="新名字")
        assert req.username == "新名字"
        assert req.email is None

    def test_email_validation(self):
        """邮箱格式不正确应报错。"""
        with pytest.raises(ValidationError):
            UpdateProfileRequest(email="not-an-email")

    def test_valid_email(self):
        req = UpdateProfileRequest(email="user@example.com")
        assert req.email == "user@example.com"

    def test_bio_too_long(self):
        """bio 超过 500 字应报错。"""
        with pytest.raises(ValidationError):
            UpdateProfileRequest(bio="a" * 501)

    def test_bio_boundary(self):
        req = UpdateProfileRequest(bio="a" * 500)
        assert req.bio is not None
        assert len(req.bio) == 500
