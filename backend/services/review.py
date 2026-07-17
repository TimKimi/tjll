"""评论业务逻辑层。"""

from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.review import Review
from backend.schemas.common import PaginatedData
from backend.schemas.review import ReviewBase, ReviewUser


def _parse_json_field(value: str | None) -> dict | None:
    """解析 JSON 字符串字段。"""
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _model_to_schema(review: Review) -> ReviewBase:
    """ORM 模型转响应 Schema。"""
    user_raw = _parse_json_field(review.user)
    user = ReviewUser(**user_raw) if user_raw else None

    return ReviewBase(
        id=review.id,
        business_id=review.business_id,
        text=review.text,
        rating=review.rating,
        time_created=review.time_created,
        user=user,
        url=review.url,
    )


class ReviewService:
    """评论服务。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_business(
        self,
        business_id: str,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "time",
    ) -> PaginatedData[ReviewBase]:
        """获取某店铺的评论列表。"""
        stmt = select(Review).where(Review.business_id == business_id)

        # 统计总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one() or 0

        # 排序
        if sort_by == "rating_high":
            stmt = stmt.order_by(Review.rating.desc())
        elif sort_by == "rating_low":
            stmt = stmt.order_by(Review.rating.asc())
        else:
            stmt = stmt.order_by(Review.time_created.desc())

        # 分页
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.db.execute(stmt)
        items = [_model_to_schema(r) for r in result.scalars().all()]

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_by_id(self, review_id: str) -> ReviewBase | None:
        """根据 ID 获取评论详情。"""
        result = await self.db.execute(select(Review).where(Review.id == review_id))
        review = result.scalar_one_or_none()
        return _model_to_schema(review) if review else None
