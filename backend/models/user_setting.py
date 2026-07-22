"""用户设置表 ORM 模型。

以 JSON 列存储设置项（key-value），新增设置项无需改表结构。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class UserSetting(Base):
    """用户配置（一对一）。"""

    __tablename__ = "user_settings"

    id: Mapped[str] = mapped_column(String(22), primary_key=True, comment="ID")
    user_id: Mapped[str] = mapped_column(
        String(22),
        ForeignKey("app_users.id"),
        unique=True,
        index=True,
        comment="用户 ID",
    )
    settings: Mapped[dict] = mapped_column(
        JSON(none_as_null=True),
        default=dict,
        comment='用户配置 JSON，如 {"insight_create": false, ...}',
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def __repr__(self) -> str:
        return f"<UserSetting user_id={self.user_id!r}>"
