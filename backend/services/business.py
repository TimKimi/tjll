"""店铺业务逻辑层。"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.business import Business
from backend.schemas.business import (
    BusinessDetail,
    BusinessListQuery,
    Category,
    Coordinates,
    Location,
)
from backend.schemas.common import PaginatedData
from backend.services.yelp_search import YelpSearchService

logger = logging.getLogger("backend.services.business")


def _parse_json_field(value: str | None) -> Any:
    """解析 JSON 字符串字段。"""
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _parse_json_list(value: str | None) -> list[str]:
    """解析 JSON 字符串数组，返回 list[str]。"""
    if not value:
        return []
    try:
        result = json.loads(value)
        if isinstance(result, list):
            return [str(item) for item in result]
        return []
    except (json.JSONDecodeError, TypeError):
        return []


def _model_to_schema(biz: Business) -> BusinessDetail:
    """ORM 模型转响应 Schema。"""
    categories_raw = _parse_json_field(biz.categories) or []
    location_raw = _parse_json_field(biz.address) or {}
    hours_raw = _parse_json_field(biz.hours)

    categories = [Category(**c) for c in categories_raw if isinstance(c, dict)]
    location = Location(**location_raw) if isinstance(location_raw, dict) else None
    coordinates = (
        Coordinates(latitude=biz.latitude, longitude=biz.longitude)
        if biz.latitude and biz.longitude
        else None
    )

    return BusinessDetail(
        id=biz.id,
        alias=biz.alias,
        name=biz.name,
        image_url=biz.image_url,
        is_closed=biz.is_closed,
        url=biz.url,
        review_count=biz.review_count,
        rating=biz.rating,
        price=biz.price,
        categories=categories,
        coordinates=coordinates,
        location=location,
        phone=biz.phone,
        display_phone=biz.display_phone,
        transactions=_parse_json_list(biz.transactions),
        photos=_parse_json_list(biz.photos),
        hours=hours_raw,
    )


class BusinessService:
    """店铺服务。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, business_id: str) -> BusinessDetail | None:
        """根据 ID 获取店铺详情。"""
        result = await self.db.execute(
            select(Business).where(Business.id == business_id)
        )
        biz = result.scalar_one_or_none()
        return _model_to_schema(biz) if biz else None

    async def list_businesses(
        self, query: BusinessListQuery
    ) -> PaginatedData[BusinessDetail]:
        """分页查询店铺列表，根据 source 参数选择数据源。"""
        if query.source == "yelp":
            return await self._search_via_yelp(query)
        else:
            return await self._search_via_db(query)

    async def _search_via_db(
        self, query: BusinessListQuery
    ) -> PaginatedData[BusinessDetail]:
        """从数据库查询店铺列表。"""
        stmt = select(Business)

        # 关键词搜索
        if query.keyword:
            stmt = stmt.where(Business.name.ilike(f"%{query.keyword}%"))

        # 分类筛选（简单包含匹配）
        if query.category:
            stmt = stmt.where(Business.categories.ilike(f"%{query.category}%"))

        # 地区筛选
        if query.location:
            stmt = stmt.where(Business.address.ilike(f"%{query.location}%"))

        # 价格筛选
        if query.price:
            stmt = stmt.where(Business.price.in_(query.price.split(",")))

        # 统计总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one() or 0

        # 排序
        if query.sort_by == "review_count":
            stmt = stmt.order_by(Business.review_count.desc())
        elif query.sort_by == "rating":
            stmt = stmt.order_by(Business.rating.desc())
        else:
            stmt = stmt.order_by(Business.rating.desc())

        # 分页
        offset = (query.page - 1) * query.page_size
        stmt = stmt.offset(offset).limit(query.page_size)

        result = await self.db.execute(stmt)
        items = [_model_to_schema(biz) for biz in result.scalars().all()]

        total_pages = (
            (total + query.page_size - 1) // query.page_size
            if query.page_size > 0
            else 0
        )

        return PaginatedData(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
        )

    async def _search_via_yelp(
        self, query: BusinessListQuery
    ) -> PaginatedData[BusinessDetail]:
        """通过 Yelp API 搜索店铺。"""
        offset = (query.page - 1) * query.page_size
        yelp_search = YelpSearchService()
        return await yelp_search.search_as_schema(
            keyword=query.keyword,
            category=query.category,
            location=query.location,
            latitude=query.latitude,
            longitude=query.longitude,
            sort_by=query.sort_by,
            price=query.price,
            limit=query.page_size,
            offset=offset,
        )
