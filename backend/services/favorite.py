"""收藏业务逻辑层：列表、添加、移除。"""

from __future__ import annotations

import json
import math
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import AppError
from backend.models.business import Business
from backend.models.favorite import Favorite
from backend.schemas.common import PaginatedData
from backend.schemas.favorite import FavoriteItem


class FavoriteService:
    """收藏服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_favorites(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> PaginatedData[FavoriteItem]:
        """获取用户收藏列表（分页，含店铺摘要信息）。

        Args:
            user_id: 用户 ID。
            page: 页码（从 1 开始）。
            page_size: 每页条数。

        Returns:
            分页的收藏项列表。
        """
        # 总数
        count_q = select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        total_result = await self.db.execute(count_q)
        total = total_result.scalar_one()

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        offset = (page - 1) * page_size

        # 分页查询，关联 Business 获取店铺信息
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
            .join(Business, Favorite.shop_id == Business.id)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows_result = await self.db.execute(q)
        rows = rows_result.all()

        items = [self._row_to_item(row) for row in rows]

        return PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def add_favorite(self, user_id: str, shop_id: str) -> FavoriteItem:
        """添加收藏。

        Raises:
            AppError: 商家不存在（404）或已收藏（409）。
        """
        # 检查商家是否存在
        biz_result = await self.db.execute(
            select(Business).where(Business.id == shop_id)
        )
        business = biz_result.scalar_one_or_none()
        if not business:
            raise AppError("商家不存在", code=404)

        # 检查是否已收藏
        existing_result = await self.db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id, Favorite.shop_id == shop_id
            )
        )
        if existing_result.scalar_one_or_none():
            raise AppError("已收藏该商家", code=409)

        # 创建收藏记录
        fav = Favorite(
            id=uuid.uuid4().hex[:22],
            user_id=user_id,
            shop_id=shop_id,
        )
        self.db.add(fav)
        await self.db.commit()
        await self.db.refresh(fav)

        return self._build_item(fav, business)

    async def remove_favorite(self, user_id: str, shop_id: str) -> None:
        """移除收藏。

        Raises:
            AppError: 收藏不存在（404）。
        """
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

    # ── 辅助方法 ──────────────────────────────────────────────

    def _row_to_item(self, row) -> FavoriteItem:
        """将 (Favorite, name, image_url, rating, price, address, categories) 行转为 FavoriteItem。"""
        fav, name, image_url, rating, price, address_json, categories_json = row
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
        """从 Favorite 和 Business 数据构造 FavoriteItem。"""
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
            name=name or "",
            image_url=image_url or "",
            rating=rating or 0.0,
            price=price or "",
            address=self._parse_address(address_json),
            category=self._parse_first_category(categories_json),
            created_at=fav.created_at,
        )

    @staticmethod
    def _parse_address(address_json: str | None) -> str:
        """解析地址 JSON，返回 address1 或空字符串。"""
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
        """解析分类 JSON，返回第一个分类的 title。"""
        if not categories_json:
            return ""
        try:
            data = json.loads(categories_json)
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("title", "")
            return str(data)
        except (json.JSONDecodeError, TypeError):
            return ""
