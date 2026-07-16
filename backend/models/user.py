"""用户表 ORM 模型。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class User(Base):
    """Yelp 用户，数据来自 yelp_academic_dataset_user.json。"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(22), primary_key=True, comment="Yelp 用户 ID"
    )
    name: Mapped[str] = mapped_column(String(255), comment="用户名")
    review_count: Mapped[int] = mapped_column(Integer, default=0, comment="评论数")
    yelping_since: Mapped[str] = mapped_column(
        String(16), default="", comment="加入 Yelp 时间"
    )
    useful: Mapped[int] = mapped_column(Integer, default=0)
    funny: Mapped[int] = mapped_column(Integer, default=0)
    cool: Mapped[int] = mapped_column(Integer, default=0)
    fans: Mapped[int] = mapped_column(Integer, default=0)
    average_stars: Mapped[float] = mapped_column(Float, default=0.0)

    # JSON 字段
    elite: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON 数组，精英年份"
    )
    friends: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON 数组，好友 ID 列表"
    )

    # ── 元信息 ──
    stored_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="入库时间"
    )

    def __repr__(self) -> str:
        return f"<User {self.id} {self.name!r}>"
