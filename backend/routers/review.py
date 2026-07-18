"""评论路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.common import ApiResponse, PaginatedData
from backend.schemas.review import ReviewBase
from backend.services.review import ReviewService

router = APIRouter(prefix="/api/review", tags=["评论"])


@router.post(
    "/list",
    summary="店铺评论列表",
    response_model=ApiResponse[PaginatedData[ReviewBase]],
)
async def review_list(
    business_id: str = Query(..., description="店铺 ID（Yelp 商家 ID）"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    sort_by: str = Query(
        default="time", description="排序：time/rating_high/rating_low"
    ),
    source: str = Query(
        default="db", description="数据来源，可选值：db（数据库）、yelp（Yelp API）"
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedData[ReviewBase]]:
    """分页查询指定店铺的评论列表（POST 方式，参数通过 Query 传递）。"""
    service = ReviewService(db)
    result = await service.list_by_business(
        business_id=business_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        source=source,
    )
    return ApiResponse.ok(data=result)


@router.post(
    "/{review_id}",
    summary="评论详情",
    response_model=ApiResponse[ReviewBase],
)
async def review_detail(
    review_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ReviewBase]:
    """根据 ID 获取评论详情（POST 方式，ID 在路径中）。"""
    service = ReviewService(db)
    review = await service.get_by_id(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="评论不存在")
    return ApiResponse.ok(data=review)
