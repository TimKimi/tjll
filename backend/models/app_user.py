"""应用用户表 ORM 模型。

独立于 Yelp 数据集的 User 模型，用于平台认证与个人管理。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class AppUser(Base):
    """平台应用用户。"""

    __tablename__ = "app_users"

    # ── 核心标识 ──
    id: Mapped[str] = mapped_column(String(22), primary_key=True, comment="用户 ID")
    username: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, comment="用户名"
    )
    password_hash: Mapped[str] = mapped_column(String(255), comment="bcrypt 密码哈希")

    # ── 个人信息 ──
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, default="", comment="邮箱"
    )
    bio: Mapped[str | None] = mapped_column(
        Text, nullable=True, default="", comment="个性签名"
    )
    avatar: Mapped[str | None] = mapped_column(
        Text, nullable=True, default="", comment="头像 URL"
    )

    # ── 密码重置 ──
    reset_token: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None, comment="密码重置令牌"
    )
    reset_token_exp: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, comment="密码重置令牌过期时间"
    )

    # ── 状态 ──
    is_online: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否在线")
    role: Mapped[str] = mapped_column(
        String(16), default="user", comment="角色：user / admin"
    )

    # ── 元信息 ──
    register_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="注册时间"
    )

    def __repr__(self) -> str:
        return f"<AppUser {self.id} {self.username!r}>"
