"""Data 数据接口服务层 —— 为其他模块提供结构化数据查询。

其他模块（如 RAG、检索、推荐）通过此服务访问数据库中的 Yelp 数据，
无需直接操作 ORM 模型。

用法：
    from backend.data.service import DataService

    svc = DataService()
    biz = await svc.get_business("some-id")
    reviews = await svc.get_reviews_by_business("some-id")
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import async_session
from backend.models.business import Business
from backend.models.review import Review


class DataService:
    """Yelp 数据查询服务。

    所有方法直接操作数据库（PostgreSQL），数据来源为 Yelp 学术数据集。

    注意：所有方法都接受可选的 session 参数。传入外部 session 时，
    直接使用该 session（不创建新事务、不关闭它）；不传时自动创建和关闭会话。
    """

    # ============================================================
    # 商家查询
    # ============================================================

    async def get_business(
        self, business_id: str, session: AsyncSession | None = None
    ) -> Business | None:
        """根据 ID 获取商家详情（含关联评论的懒加载代理）。"""
        if session:
            return await session.get(Business, business_id)
        async with async_session() as s:
            return await s.get(Business, business_id)

    async def list_businesses(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        keyword: str | None = None,
        min_rating: float | None = None,
        category: str | None = None,
        sort_by: str = "review_count",
        session: AsyncSession | None = None,
    ) -> tuple[list[Business], int]:
        """搜索/列出商家，支持过滤和排序。

        Args:
            skip: 偏移量。
            limit: 返回条数（最大 100）。
            keyword: 按名称关键词搜索。
            min_rating: 最低评分过滤。
            category: 按分类别名搜索（JSON categories 字段中模糊匹配）。
            sort_by: 排序字段（review_count, rating, name, stored_at）。
            session: 可选外部会话。

        Returns:
            (商家列表, 总数)
        """
        limit = min(limit, 100)
        conditions: list[Any] = []
        if keyword:
            conditions.append(Business.name.ilike(f"%{keyword}%"))
        if min_rating is not None:
            conditions.append(Business.rating >= min_rating)
        if category and category.strip():
            conditions.append(Business.categories.ilike(f"%{category.strip()}%"))

        base_query = select(Business)
        if conditions:
            base_query = base_query.where(*conditions)

        count_query = select(func.count()).select_from(base_query.subquery())

        sort_map: dict[str, Any] = {
            "review_count": Business.review_count.desc(),
            "rating": Business.rating.desc(),
            "name": Business.name.asc(),
            "stored_at": Business.stored_at.desc(),
        }
        base_query = base_query.order_by(
            sort_map.get(sort_by, Business.review_count.desc())
        )
        base_query = base_query.offset(skip).limit(limit)

        if session:
            total = await session.scalar(count_query) or 0
            result = await session.execute(base_query)
            businesses = list(result.scalars().all())
            return businesses, total

        async with async_session() as s:
            total = await s.scalar(count_query) or 0
            result = await s.execute(base_query)
            businesses = list(result.scalars().all())
            await s.commit()
            return businesses, total

    async def get_business_with_reviews(
        self, business_id: str, session: AsyncSession | None = None
    ) -> dict[str, Any] | None:
        """获取商家详情及其所有评论。"""
        stmt = (
            select(Business)
            .where(Business.id == business_id)
            .options(selectinload(Business.reviews))
        )

        if session:
            result = await session.execute(stmt)
        else:
            async with async_session() as s:
                result = await s.execute(stmt)

        biz = result.scalar_one_or_none()
        if biz is None:
            return None

        return {
            "business": _business_to_dict(biz),
            "reviews": [_review_to_dict(r) for r in biz.reviews],
        }

    # ============================================================
    # 评论查询
    # ============================================================

    async def get_reviews_by_business(
        self,
        business_id: str,
        *,
        skip: int = 0,
        limit: int = 20,
        session: AsyncSession | None = None,
    ) -> tuple[list[Review], int]:
        """获取某商家的所有评论。

        Returns:
            (评论列表, 总数)
        """
        limit = min(limit, 100)
        base_query = (
            select(Review)
            .where(Review.business_id == business_id)
            .order_by(Review.time_created.desc())
        )
        count_query = (
            select(func.count())
            .select_from(Review)
            .where(Review.business_id == business_id)
        )

        if session:
            total = await session.scalar(count_query) or 0
            result = await session.execute(base_query.offset(skip).limit(limit))
            return list(result.scalars().all()), total

        async with async_session() as s:
            total = await s.scalar(count_query) or 0
            result = await s.execute(base_query.offset(skip).limit(limit))
            return list(result.scalars().all()), total

    async def get_review(
        self, review_id: str, session: AsyncSession | None = None
    ) -> Review | None:
        """根据 ID 获取单条评论。"""
        if session:
            return await session.get(Review, review_id)
        async with async_session() as s:
            return await s.get(Review, review_id)

    # ============================================================
    # 统计
    # ============================================================

    async def get_stats(self, session: AsyncSession | None = None) -> dict[str, Any]:
        """获取数据统计信息。"""
        if session:
            return await self._query_stats(session)
        async with async_session() as s:
            return await self._query_stats(s)

    @staticmethod
    async def _query_stats(session: AsyncSession) -> dict[str, Any]:
        """在给定会话中查询统计。"""
        biz_count = (
            await session.execute(text("SELECT COUNT(*) FROM businesses"))
        ).scalar() or 0
        rev_count = (
            await session.execute(text("SELECT COUNT(*) FROM reviews"))
        ).scalar() or 0
        avg_rating = (
            await session.execute(
                text(
                    "SELECT ROUND(AVG(rating)::numeric, 2) "
                    "FROM businesses WHERE rating > 0"
                )
            )
        ).scalar()
        closed_count = (
            await session.execute(
                text("SELECT COUNT(*) FROM businesses WHERE is_closed = TRUE")
            )
        ).scalar() or 0

        return {
            "businesses": biz_count,
            "reviews": rev_count,
            "avg_rating": float(avg_rating) if avg_rating else 0.0,
            "closed_businesses": closed_count,
        }

    # ============================================================
    # 批量 / 原始查询（供 RAG 等其他模块使用）
    # ============================================================

    async def get_all_business_ids(
        self, session: AsyncSession | None = None
    ) -> list[str]:
        """获取所有商家 ID（供 RAG 批量处理用）。"""
        stmt = select(Business.id)
        if session:
            result = await session.execute(stmt)
        else:
            async with async_session() as s:
                result = await s.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_reviews_texts_by_business(
        self,
        business_id: str,
        limit: int = 50,
        session: AsyncSession | None = None,
    ) -> list[str]:
        """获取某商家的评论文本列表（供 RAG 检索用）。"""
        stmt = select(Review.text).where(Review.business_id == business_id).limit(limit)
        if session:
            result = await session.execute(stmt)
        else:
            async with async_session() as s:
                result = await s.execute(stmt)
        return [row[0] for row in result.all()]


# ============================================================
# 序列化辅助
# ============================================================


def _business_to_dict(biz: Business) -> dict[str, Any]:
    """将 Business ORM 对象转为可 JSON 序列化的字典。"""
    data = {
        "id": biz.id,
        "alias": biz.alias,
        "name": biz.name,
        "image_url": biz.image_url,
        "is_closed": biz.is_closed,
        "url": biz.url,
        "review_count": biz.review_count,
        "rating": biz.rating,
        "price": biz.price,
        "categories": _safe_json_load(biz.categories),
        "latitude": biz.latitude,
        "longitude": biz.longitude,
        "address": _safe_json_load(biz.address),
        "phone": biz.phone,
        "display_phone": biz.display_phone,
        "hours": _safe_json_load(biz.hours),
        "transactions": _safe_json_load(biz.transactions),
        "photos": _safe_json_load(biz.photos),
        "stored_at": biz.stored_at.isoformat() if biz.stored_at else None,
        "updated_at": biz.updated_at.isoformat() if biz.updated_at else None,
    }
    return data


def _review_to_dict(review: Review) -> dict[str, Any]:
    """将 Review ORM 对象转为可 JSON 序列化的字典。"""
    return {
        "id": review.id,
        "business_id": review.business_id,
        "url": review.url,
        "text": review.text,
        "rating": review.rating,
        "time_created": review.time_created,
        "user": _safe_json_load(review.user),
        "stored_at": review.stored_at.isoformat() if review.stored_at else None,
    }


def _safe_json_load(value: str | None) -> Any:
    """安全地解析 JSON 字符串，解析失败返回原值。"""
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value
