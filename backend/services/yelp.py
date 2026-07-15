"""Yelp Fusion API 异步客户端 —— 数据获取、验证、存储。"""

from __future__ import annotations

from json import dumps
from typing import Any

from httpx import AsyncClient

from backend.config import settings
from backend.database import async_session
from backend.models.business import Business
from backend.models.review import Review
from backend.schemas.yelp import (
    YelpBusiness,
    YelpBusinessSearchResponse,
    YelpReview,
    YelpReviewsResponse,
)


class YelpError(Exception):
    """Yelp API 调用异常。"""

    def __init__(self, status_code: int, code: str, description: str) -> None:
        self.status_code = status_code
        self.code = code
        self.description = description
        super().__init__(f"[{status_code}] {code}: {description}")


class YelpService:
    """Yelp API 调用 + 本地持久化。

    使用方式：
        svc = YelpService()
        result = await svc.search_businesses(location="New York")
    """

    def __init__(self) -> None:
        self._base_url = settings.YELP_API_BASE_URL
        self._headers = {
            "Authorization": f"Bearer {settings.YELP_API_KEY}",
            "Accept": "application/json",
        }

    # ── HTTP 请求 ──────────────────────────────────────────

    async def _get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """通用 GET 请求，自动处理错误。"""
        async with AsyncClient(base_url=self._base_url) as client:
            resp = await client.get(path, headers=self._headers, params=params)
            if resp.is_success:
                return resp.json()
            body = resp.json()
            err = body.get("error", {})
            raise YelpError(
                status_code=resp.status_code,
                code=err.get("code", "UNKNOWN"),
                description=err.get("description", str(resp.text)),
            )

    # ── API 调用 ───────────────────────────────────────────

    async def search_businesses(
        self,
        location: str | None = None,
        term: str | None = None,
        categories: str | None = None,
        limit: int = 20,
        offset: int = 0,
        **kwargs: Any,
    ) -> YelpBusinessSearchResponse:
        """搜索商家。

        Args:
            location: 地点，如 "New York City"。
            term: 搜索词，如 "food"、 "pizza"。
            categories: 分类过滤，逗号分隔。
            limit: 返回数量（0~50）。
            offset: 偏移量。

        Returns:
            搜索结果。
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset, **kwargs}
        if location:
            params["location"] = location
        if term:
            params["term"] = term
        if categories:
            params["categories"] = categories

        data = await self._get("/businesses/search", params)
        return YelpBusinessSearchResponse(**data)

    async def get_business(self, business_id: str) -> YelpBusiness:
        """获取单个商家详情。

        Args:
            business_id: Yelp 商家 ID。

        Returns:
            商家详细信息。
        """
        data = await self._get(f"/businesses/{business_id}")
        return YelpBusiness(**data)

    async def get_reviews(
        self,
        business_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> YelpReviewsResponse:
        """获取商家评论。

        Args:
            business_id: Yelp 商家 ID。
            limit: 返回数量。
            offset: 偏移量。

        Returns:
            评论列表。
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._get(f"/businesses/{business_id}/reviews", params)
        return YelpReviewsResponse(**data)

    # ── 数据持久化 ─────────────────────────────────────────

    async def save_business(self, biz: YelpBusiness) -> Business:
        """将商家数据存入数据库（存在则更新）。"""
        async with async_session() as session:
            existing = await session.get(Business, biz.id)
            if existing:
                # 更新现有记录
                existing.name = biz.name
                existing.alias = biz.alias
                existing.image_url = biz.image_url
                existing.is_closed = biz.is_closed
                existing.url = biz.url
                existing.review_count = biz.review_count
                existing.rating = biz.rating
                existing.price = biz.price
                existing.categories = (
                    dumps([c.model_dump() for c in biz.categories])
                    if biz.categories
                    else None
                )
                existing.latitude = (
                    biz.coordinates.latitude if biz.coordinates else None
                )
                existing.longitude = (
                    biz.coordinates.longitude if biz.coordinates else None
                )
                existing.address = (
                    dumps(biz.location.model_dump()) if biz.location else None
                )
                existing.phone = biz.phone
                existing.display_phone = biz.display_phone
                existing.hours = dumps(biz.hours.model_dump()) if biz.hours else None
                existing.transactions = (
                    dumps(biz.transactions) if biz.transactions else None
                )
                existing.photos = dumps(biz.photos) if biz.photos else None
                existing.yelp_menu_url = biz.yelp_menu_url
                biz_obj = existing
            else:
                biz_obj = Business(
                    id=biz.id,
                    alias=biz.alias,
                    name=biz.name,
                    image_url=biz.image_url,
                    is_closed=biz.is_closed,
                    url=biz.url,
                    review_count=biz.review_count,
                    rating=biz.rating,
                    price=biz.price,
                    categories=dumps([c.model_dump() for c in biz.categories])
                    if biz.categories
                    else None,
                    latitude=biz.coordinates.latitude if biz.coordinates else None,
                    longitude=biz.coordinates.longitude if biz.coordinates else None,
                    address=dumps(biz.location.model_dump()) if biz.location else None,
                    phone=biz.phone,
                    display_phone=biz.display_phone,
                    hours=dumps(biz.hours.model_dump()) if biz.hours else None,
                    transactions=dumps(biz.transactions) if biz.transactions else None,
                    photos=dumps(biz.photos) if biz.photos else None,
                    yelp_menu_url=biz.yelp_menu_url,
                )
                session.add(biz_obj)
            await session.commit()
            await session.refresh(biz_obj)
            return biz_obj

    async def save_review(self, business_id: str, review: YelpReview) -> Review:
        """将评论数据存入数据库（存在则跳过）。"""
        async with async_session() as session:
            existing = await session.get(Review, review.id)
            if existing:
                await session.close()
                return existing
            review_obj = Review(
                id=review.id,
                business_id=business_id,
                url=review.url,
                text=review.text,
                rating=review.rating,
                time_created=review.time_created,
                user=dumps(review.user.model_dump()) if review.user else None,
            )
            session.add(review_obj)
            await session.commit()
            await session.refresh(review_obj)
            return review_obj

    async def fetch_and_store(
        self,
        location: str,
        term: str | None = None,
        categories: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """完整流程：搜索商家 → 获取详情 → 获取评论 → 存入数据库。

        Returns:
            统计信息：搜索了多少、成功存储了多少。
        """
        # Step 1: 搜索商家
        search_result = await self.search_businesses(
            location=location,
            term=term,
            categories=categories,
            limit=limit,
        )
        stats: dict[str, Any] = {
            "location": location,
            "term": term,
            "total_found": search_result.total,
            "businesses_stored": 0,
            "reviews_stored": 0,
            "businesses": [],
        }

        # Step 2: 逐个获取详情 + 评论并存储
        for biz_summary in search_result.businesses:
            try:
                biz_detail = await self.get_business(biz_summary.id)
                await self.save_business(biz_detail)
                stats["businesses_stored"] += 1
                stats["businesses"].append(
                    {
                        "id": biz_detail.id,
                        "name": biz_detail.name,
                        "rating": biz_detail.rating,
                        "review_count": biz_detail.review_count,
                    }
                )
            except YelpError as exc:
                print(f"  ⚠  {biz_summary.id} {biz_summary.name}: {exc}")
                continue

                # 获取评论（Reviews 端点可能需要更高套餐，不可用则跳过）
                try:
                    reviews_result = await self.get_reviews(biz_summary.id)
                    for r in reviews_result.reviews:
                        await self.save_review(biz_summary.id, r)
                        stats["reviews_stored"] += 1
                except YelpError:
                    pass

        return stats
