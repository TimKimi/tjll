"""收藏表 ORM 模型。

每个收藏记录关联一个用户（app_users）和一个商家（businesses）。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class Favorite(Base):
    """用户收藏的商家。"""

    __tablename__ = "favorites"

    # ── 核心标识 ──
    id: Mapped[str] = mapped_column(String(22), primary_key=True, comment="收藏记录 ID")
    user_id: Mapped[str] = mapped_column(
        String(22),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        index=True,
        comment="用户 ID",
    )
    shop_id: Mapped[str] = mapped_column(
        String(22),
        index=True,
        comment="商家 ID（对应 businesses.id）",
    )

    # ── 元信息 ──
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="收藏时间"
    )

    def __repr__(self) -> str:
        return f"<Favorite {self.id} user={self.user_id} shop={self.shop_id}>"
