"""Yelp 搜索适配器 —— 将 Yelp API 数据转换为业务 Schema。"""

from __future__ import annotations

from backend.schemas.business import BusinessDetail, Category, Coordinates, Location
from backend.schemas.common import PaginatedData
from backend.services.yelp import YelpService
from typing import Any  # 确保顶部导入


class YelpSearchService:
    """专门负责从 Yelp 搜索并转换为统一分页结果。"""

    def __init__(self, yelp_service: YelpService | None = None):
        self._yelp = yelp_service or YelpService()

    async def search_as_schema(
        self,
        keyword: str | None = None,
        category: str | None = None,
        location: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        sort_by: str = "rating",
        price: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> PaginatedData[BusinessDetail]:
        # 1. 校验位置
        if not location and (latitude is None or longitude is None):
            raise ValueError("使用 Yelp 搜索时必须提供 location 或 latitude+longitude")

        # 2. 构建参数字典，显式声明类型为 dict[str, Any]
        params: dict[str, Any] = {
            "limit": min(limit, 50),
            "offset": offset,
        }
        if location:
            params["location"] = location
        if keyword:
            params["term"] = keyword
        if category:
            params["categories"] = category
        if price:
            params["price"] = price
        if latitude is not None and longitude is not None:
            params["latitude"] = latitude
            params["longitude"] = longitude

        sort_map = {
            "rating": "rating",
            "review_count": "review_count",
            "distance": "distance",
        }
        params["sort_by"] = sort_map.get(sort_by, "rating")

        result = await self._yelp.search_businesses(**params)

        # ---------- 4. 转换结果 ----------
        items = [self._to_business_detail(biz) for biz in result.businesses]
        total = result.total
        total_pages = (total + limit - 1) // limit if limit > 0 else 0
        page = offset // limit + 1 if limit > 0 else 1

        return PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
        )

    @staticmethod
    def _to_business_detail(biz) -> BusinessDetail:
        """将 Yelp Business 对象（来自 yelp.py 的 YelpBusiness）转换为 BusinessDetail。"""
        categories = [
            Category(alias=c.alias, title=c.title) for c in (biz.categories or [])
        ]
        location = None
        if biz.location:
            location = Location(
                address1=biz.location.address1,
                city=biz.location.city,
                state=biz.location.state,
                zip_code=biz.location.zip_code,
                country=biz.location.country,
                display_address=biz.location.display_address or [],
            )
        coordinates = None
        if biz.coordinates:
            coordinates = Coordinates(
                latitude=biz.coordinates.latitude,
                longitude=biz.coordinates.longitude,
            )
        return BusinessDetail(
            id=biz.id,
            alias=biz.alias or "",
            name=biz.name,
            image_url=biz.image_url,
            is_closed=biz.is_closed or False,
            url=biz.url,
            review_count=biz.review_count or 0,
            rating=biz.rating or 0.0,
            price=biz.price,
            categories=categories,
            coordinates=coordinates,
            location=location,
            phone=biz.phone or "",
            display_phone=biz.display_phone or "",
            transactions=biz.transactions or [],
            photos=biz.photos or [],
            hours=None,  # 搜索接口不返回 hours
        )
