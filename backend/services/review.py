"""评论业务逻辑层。"""

from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from backend.models.review import Review
from backend.schemas.common import PaginatedData
from backend.schemas.review import ReviewBase, ReviewUser
from backend.services.yelp import YelpService, YelpError


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
    user = None
    if user_raw:
        # 确保必填字段存在，缺失则用默认值
        user_raw.setdefault("name", "")
        user_raw.setdefault("profile_url", "")
        # id 如果缺失也可以用空字符串
        user = ReviewUser(**user_raw)

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
        self._yelp = YelpService()

    async def list_by_business(
        self,
        business_id: str,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "time",
        source: str = "db",
    ) -> PaginatedData[ReviewBase]:
        """获取某店铺的评论列表，根据 source 选择数据源。"""
        if source == "yelp":
            return await self._search_via_yelp(business_id, page, page_size, sort_by)
        else:
            return await self._search_via_db(business_id, page, page_size, sort_by)

    async def _search_via_db(
        self,
        business_id: str,
        page: int,
        page_size: int,
        sort_by: str,
    ) -> PaginatedData[ReviewBase]:
        """原有数据库查询逻辑。"""
        stmt = select(Review).where(Review.business_id == business_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one() or 0

        if sort_by == "rating_high":
            stmt = stmt.order_by(Review.rating.desc())
        elif sort_by == "rating_low":
            stmt = stmt.order_by(Review.rating.asc())
        else:
            stmt = stmt.order_by(Review.time_created.desc())

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

    async def _search_via_yelp(
        self,
        business_id: str,
        page: int,
        page_size: int,
        sort_by: str,
    ) -> PaginatedData[ReviewBase]:
        """
        通过 Yelp API 获取评论。
        注意：Yelp 评论接口不支持排序参数，默认按时间倒序。
        """
        offset = (page - 1) * page_size
        try:
            response = await self._yelp.get_reviews(
                business_id=business_id,
                limit=min(page_size, 50),  # Yelp 最大 50
                offset=offset,
            )
        except YelpError as e:
            raise HTTPException(status_code=e.status_code, detail=e.description)

        items = []
        for yelp_review in response.reviews:
            user = None
            if yelp_review.user:
                user = ReviewUser(
                    id=yelp_review.user.id,
                    name=yelp_review.user.name,
                    profile_url=yelp_review.user.profile_url or "",
                    image_url=yelp_review.user.image_url,
                )
            items.append(
                ReviewBase(
                    id=yelp_review.id,
                    business_id=business_id,
                    text=yelp_review.text,
                    rating=yelp_review.rating,
                    time_created=yelp_review.time_created,
                    user=user,
                    url=yelp_review.url or "",
                )
            )

        # Yelp 评论接口可能不返回 total，用当前页数量近似
        total = getattr(response, "total", len(items)) or len(items)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_by_id(self, review_id: str) -> ReviewBase | None:
        """根据 ID 获取评论详情（仅数据库）。"""
        result = await self.db.execute(select(Review).where(Review.id == review_id))
        review = result.scalar_one_or_none()
        return _model_to_schema(review) if review else None
