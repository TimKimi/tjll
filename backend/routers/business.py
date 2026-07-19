"""店铺路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.business import BusinessDetail, BusinessListQuery
from backend.schemas.common import ApiResponse, PaginatedData
from backend.services.business import BusinessService

router = APIRouter(prefix="/api/business", tags=["店铺"])


@router.post(  # 改为 POST
    "/list",
    summary="店铺列表",
    response_model=ApiResponse[PaginatedData[BusinessDetail]],
)
async def business_list(
    keyword: str | None = Query(default=None, description="搜索关键词"),
    category: str | None = Query(default=None, description="分类别名"),
    location: str | None = Query(default=None, description="城市/地区"),
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
    sort_by: str = Query(default="rating", description="排序：rating/review_count"),
    price: str | None = Query(default=None, description="价格区间，如 1,2,3"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    source: str = Query(
        default="db", description="数据来源，可选值：db（数据库）、yelp（Yelp API）"
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedData[BusinessDetail]]:
    """分页查询店铺列表，支持关键词、分类、地区筛选（POST 方式，参数通过 Query 传递）。"""
    query = BusinessListQuery(
        keyword=keyword,
        category=category,
        location=location,
        latitude=latitude,
        longitude=longitude,
        sort_by=sort_by,
        price=price,
        page=page,
        page_size=page_size,
        source=source,
    )
    service = BusinessService(db)
    result = await service.list_businesses(query)
    return ApiResponse.ok(data=result)


@router.post(  # 改为 POST，路径保持不变
    "/{business_id}",
    summary="店铺详情",
    response_model=ApiResponse[BusinessDetail],
)
async def business_detail(
    business_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[BusinessDetail]:
    """根据 ID 获取店铺详情（POST 方式，ID 在路径中）。"""
    service = BusinessService(db)
    biz = await service.get_by_id(business_id)
    if not biz:
        raise HTTPException(status_code=404, detail="店铺不存在")
    return ApiResponse.ok(data=biz)
