"""商家表 ORM 模型。"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.review import Review


class Business(Base):
    """商家，对应 Yelp Business。"""

    __tablename__ = "businesses"

    # ── 核心标识 ──
    id: Mapped[str] = mapped_column(
        String(22), primary_key=True, comment="Yelp 商家 ID"
    )
    alias: Mapped[str] = mapped_column(String(255), comment="Yelp 别名")
    name: Mapped[str] = mapped_column(String(255), index=True, comment="商家名称")

    # ── 基础信息 ──
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_closed: Mapped[bool] = mapped_column(default=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    price: Mapped[str | None] = mapped_column(String(4), nullable=True)

    # ── 分类（JSON 存储） ──
    categories: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='JSON，如 [{"alias":"pizza","title":"Pizza"}]',
    )

    # ── 位置 ──
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON，location 字段"
    )

    # ── 联系方式 ──
    phone: Mapped[str] = mapped_column(String(30), default="")
    display_phone: Mapped[str] = mapped_column(String(30), default="")

    # ── 营业时间（JSON 存储） ──
    business_hours: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON，business_hours 字段"
    )

    # ── 其他 ──
    transactions: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment='JSON，如 ["pickup","delivery"]'
    )
    photos: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JSON 数组")
    yelp_menu_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── 向量嵌入（RAG 用） ──
    embedding: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="pgvector 向量，存为字符串"
    )

    # ── 元信息 ──
    stored_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="首次入库时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="最近更新时间",
    )

    # ── 关联 ──
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="business", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Business {self.id} {self.name!r}>"
