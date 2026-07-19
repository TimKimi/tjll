"""安全工具（密码哈希、JWT）单元测试。"""

from __future__ import annotations

from datetime import timedelta

from jose import jwt

from backend.config import settings
from backend.core.security import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """测试密码哈希与验证。"""

    def test_hash_password_returns_string(self):
        hashed = hash_password("my_secret_pw")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_differs_from_plain(self):
        hashed = hash_password("password123")
        assert hashed != "password123"

    def test_verify_password_correct(self):
        hashed = hash_password("correct_pw")
        assert verify_password("correct_pw", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("real_pw")
        assert verify_password("wrong_pw", hashed) is False

    def test_same_password_different_hashes(self):
        """同一密码每次哈希结果应不同（bcrypt 加盐）。"""
        hash1 = hash_password("same_pw")
        hash2 = hash_password("same_pw")
        assert hash1 != hash2

    def test_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True


class TestJWTToken:
    """测试 JWT 签发与解码。"""

    def test_create_token_returns_string(self):
        token = create_token({"sub": "u_abc123"})
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT 三段式

    def test_decode_token_valid(self):
        token = create_token({"sub": "u_test", "role": "user"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "u_test"
        assert payload["role"] == "user"

    def test_decode_token_invalid(self):
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_decode_token_expired(self):
        """过期 token 应返回 None。"""
        token = create_token({"sub": "u_expired"}, expires_delta=timedelta(seconds=-1))
        payload = decode_token(token)
        assert payload is None

    def test_token_contains_exp_claim(self):
        token = create_token({"sub": "u_claim"})
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        assert "exp" in payload

    def test_token_with_custom_expiry(self):
        token = create_token({"sub": "u_custom"}, expires_delta=timedelta(hours=1))
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        assert "exp" in payload

    def test_create_token_with_additional_claims(self):
        token = create_token({"sub": "u_extra", "name": "张三", "role": "admin"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["name"] == "张三"
        assert payload["role"] == "admin"
