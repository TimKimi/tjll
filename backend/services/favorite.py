"""收藏业务逻辑层：列表、添加、移除。"""

from __future__ import annotations

import json
import logging
import math
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import AppError
from backend.models.business import Business
from backend.models.favorite import Favorite
from backend.schemas.common import PaginatedData
from backend.schemas.favorite import FavoriteItem
from backend.schemas.yelp import YelpBusiness
from backend.services.yelp import YelpService

logger = logging.getLogger("backend.services.favorite")


class FavoriteService:
    """收藏服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_favorites(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> PaginatedData[FavoriteItem]:
        """获取用户收藏列表（分页，含店铺摘要信息）。"""
        count_q = select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        total_result = await self.db.execute(count_q)
        total = total_result.scalar_one()

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        offset = (page - 1) * page_size

        q = (
            select(
                Favorite,
                Business.name,
                Business.image_url,
                Business.rating,
                Business.price,
                Business.address,
                Business.categories,
            )
            .join(Business, Favorite.shop_id == Business.id, isouter=True)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows_result = await self.db.execute(q)
        rows = rows_result.all()

        items = [self._row_to_item(row) for row in rows]
        logger.info("查询收藏列表 user_id=%s total=%d", user_id, total)

        return PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def add_favorite(
        self, user_id: str, shop_id: str, source: str = "db"
    ) -> FavoriteItem:
        """添加收藏。

        根据 source 选择验证方式：
        - db：查询本地 business 表
        - yelp：调用 Yelp API 验证
        """
        fav = Favorite(
            id=uuid.uuid4().hex[:22],
            user_id=user_id,
            shop_id=shop_id,
            source=source,
        )

        if source == "yelp":
            item = await self._add_from_yelp(fav, shop_id)
        else:
            item = await self._add_from_db(fav, shop_id)

        logger.info(
            "添加收藏 user_id=%s shop_id=%s source=%s", user_id, shop_id, source
        )
        return item

    async def _add_from_db(self, fav: Favorite, shop_id: str) -> FavoriteItem:
        """从本地数据库验证并添加收藏。"""
        biz_result = await self.db.execute(
            select(Business).where(Business.id == shop_id)
        )
        business = biz_result.scalar_one_or_none()
        if not business:
            raise AppError("商家不存在", code=404)

        existing = await self.db.execute(
            select(Favorite).where(
                Favorite.user_id == fav.user_id, Favorite.shop_id == shop_id
            )
        )
        if existing.scalar_one_or_none():
            raise AppError("已收藏该商家", code=409)

        self.db.add(fav)
        await self.db.commit()
        await self.db.refresh(fav)
        return self._build_item(fav, business)

    async def _add_from_yelp(self, fav: Favorite, shop_id: str) -> FavoriteItem:
        """从 Yelp API 验证并添加收藏。"""
        yelp = YelpService()
        try:
            biz = await yelp.get_business(shop_id)
        except Exception:
            raise AppError("商家不存在", code=404)

        existing = await self.db.execute(
            select(Favorite).where(
                Favorite.user_id == fav.user_id, Favorite.shop_id == shop_id
            )
        )
        if existing.scalar_one_or_none():
            raise AppError("已收藏该商家", code=409)

        self.db.add(fav)
        await self.db.commit()
        await self.db.refresh(fav)
        return self._build_item_from_yelp(fav, biz)

    async def remove_favorite(self, user_id: str, shop_id: str) -> None:
        """移除收藏。"""
        result = await self.db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id, Favorite.shop_id == shop_id
            )
        )
        fav = result.scalar_one_or_none()
        if not fav:
            raise AppError("收藏不存在", code=404)

        await self.db.delete(fav)
        await self.db.commit()
        logger.info("移除收藏 user_id=%s shop_id=%s", user_id, shop_id)

    # ── 辅助方法 ──────────────────────────────────────────────

    def _row_to_item(self, row) -> FavoriteItem:
        fav, name, image_url, rating, price, address_json, categories_json = row

        if fav.source == "yelp":
            return FavoriteItem(
                id=fav.id,
                shop_id=fav.shop_id,
                source=fav.source,
                name=name or "",
                image_url=image_url or "",
                rating=rating or 0.0,
                price=price or "",
                address=address_json or "",
                category=categories_json or "",
                created_at=fav.created_at,
            )

        return self._build_item(
            fav,
            name=name,
            image_url=image_url,
            rating=rating,
            price=price,
            address_json=address_json,
            categories_json=categories_json,
        )

    def _build_item(
        self,
        fav: Favorite,
        business: Business | None = None,
        name: str | None = None,
        image_url: str | None = None,
        rating: float | None = None,
        price: str | None = None,
        address_json: str | None = None,
        categories_json: str | None = None,
    ) -> FavoriteItem:
        if business is not None:
            name = business.name
            image_url = business.image_url
            rating = business.rating
            price = business.price
            address_json = business.address
            categories_json = business.categories

        return FavoriteItem(
            id=fav.id,
            shop_id=fav.shop_id,
            source=fav.source,
            name=name or "",
            image_url=image_url or "",
            rating=rating or 0.0,
            price=price or "",
            address=self._parse_address(address_json),
            category=self._parse_first_category(categories_json),
            created_at=fav.created_at,
        )

    @staticmethod
    def _build_item_from_yelp(fav: Favorite, biz: YelpBusiness) -> FavoriteItem:
        """从 Yelp API 响应构建收藏项。"""
        location = biz.location
        categories = biz.categories or []
        return FavoriteItem(
            id=fav.id,
            shop_id=fav.shop_id,
            source=fav.source,
            name=biz.name or "",
            image_url=biz.image_url or "",
            rating=biz.rating or 0.0,
            price=biz.price or "",
            address=(location.address1 or "") if location else "",
            category=categories[0].title if categories else "",
            created_at=fav.created_at,
        )

    @staticmethod
    def _parse_address(address_json: str | None) -> str:
        if not address_json:
            return ""
        try:
            data = json.loads(address_json)
            if isinstance(data, dict):
                return data.get("address1") or data.get("display_address", "")
            return str(data)
        except (json.JSONDecodeError, TypeError):
            return ""

    @staticmethod
    def _parse_first_category(categories_json: str | None) -> str:
        if not categories_json:
            return ""
        try:
            data = json.loads(categories_json)
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("title", "")
            return str(data)
        except (json.JSONDecodeError, TypeError):
            return ""
