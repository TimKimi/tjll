"""用户设置表 ORM 模型。

每个设置项都是独立字段，新增设置在模型和 schema 同步加字段即可。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class UserSetting(Base):
    """用户配置（一对一）。"""

    __tablename__ = "user_settings"

    id: Mapped[str] = mapped_column(String(22), primary_key=True, comment="ID")
    user_id: Mapped[str] = mapped_column(
        String(22),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        comment="用户 ID",
    )
    insight_create: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否开启洞察创建"
    )
    insight_use: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否使用历史洞察"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def __repr__(self) -> str:
        return f"<UserSetting user_id={self.user_id!r}>"
