"""密码哈希与 JWT 工具。

依赖 `passlib[bcrypt]` 和 `python-jose[cryptography]`。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import settings

# ── 密码哈希 ───────────────────────────────────────────────

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希。"""
    return _pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """验证明文密码是否匹配哈希值。"""
    return _pwd_ctx.verify(plain, hashed)


# ── JWT ────────────────────────────────────────────────────


def create_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """签发 JWT。

    Args:
        data: 要放入 payload 的声明（至少包含 ``sub``）。
        expires_delta: 过期时间，默认取配置的 JWT_EXPIRE_MINUTES。

    Returns:
        编码后的 JWT 字符串。
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """解码并验证 JWT。

    Args:
        token: JWT 字符串。

    Returns:
        payload 字典，若 token 无效或已过期则返回 None。
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
