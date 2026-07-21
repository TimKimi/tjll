"""认证配置 — JWT 密钥、过期时间。"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from pydantic import Field, field_validator


class AuthMixin:
    """JWT 认证配置。

    所有默认值在此统一修改。
    """

    # ── JWT ──────────────────────────────────────────────────
    # [必填] JWT 签名密钥，生产环境务必使用高强度随机字符串
    JWT_SECRET: str = Field(default="change-me-in-production")
    # JWT 签名算法
    JWT_ALGORITHM: str = "HS256"
    # Token 过期时间（分钟），默认 1440 = 24 小时
    JWT_EXPIRE_MINUTES: int = 1440
    # Refresh Token 过期时间（天）
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    # 注册时是否检查邮箱域名可送达性（生产环境可开启）
    EMAIL_CHECK_DELIVERABILITY: bool = False

    # ── 解析器 ───────────────────────────────────────────────

    @field_validator("JWT_EXPIRE_MINUTES", mode="before")
    @classmethod
    def _parse_jwt_expire(cls, v: Any) -> int:
        """支持 ``60 * 24`` 这类表达式写法。"""
        if isinstance(v, str) and "*" in v:
            parts = v.split("*")
            try:
                return int(parts[0].strip()) * int(parts[1].strip())
            except (ValueError, IndexError):
                pass
        return int(v) if v is not None else 1440

    # ── 派生属性 ─────────────────────────────────────────────

    @property
    def jwt_expire_delta(self) -> timedelta:
        """JWT 过期时间差。"""
        return timedelta(minutes=self.JWT_EXPIRE_MINUTES)
