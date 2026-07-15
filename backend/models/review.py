"""评论表 ORM 模型。"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.business import Business


class Review(Base):
    """评论，关联到商家。"""

    __tablename__ = "reviews"

    # ── 核心标识 ──
    id: Mapped[str] = mapped_column(
        String(22), primary_key=True, comment="Yelp 评论 ID"
    )
    business_id: Mapped[str] = mapped_column(
        String(22),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        index=True,
        comment="所属商家 Yelp ID",
    )

    # ── 评论内容 ──
    url: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text, comment="评论文本")
    rating: Mapped[int] = mapped_column(Integer, comment="评分 1~5")
    time_created: Mapped[str] = mapped_column(
        String(30), comment="Yelp 返回的时间字符串"
    )

    # ── 用户信息（JSON 存储） ──
    user: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON，user 字段"
    )

    # ── 向量嵌入（RAG 用） ──
    embedding: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="pgvector 向量，存为字符串"
    )

    # ── 元信息 ──
    stored_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="入库时间"
    )

    # ── 关联 ──
    business: Mapped["Business"] = relationship("Business", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review {self.id} business={self.business_id}>"
