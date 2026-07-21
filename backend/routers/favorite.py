"""收藏路由：列表、添加、移除。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user
from backend.core.exceptions import AppError
from backend.database import get_db
from backend.schemas.common import ApiResponse, PaginatedData
from backend.schemas.favorite import AddFavoriteRequest, FavoriteItem
from backend.services.favorite import FavoriteService

router = APIRouter(prefix="/api/favorites", tags=["收藏"])


@router.get(
    "",
    summary="获取收藏列表",
    response_model=ApiResponse[PaginatedData[FavoriteItem]],
)
async def list_favorites(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedData[FavoriteItem]]:
    """获取当前用户的收藏列表（分页）。"""
    service = FavoriteService(db)
    result = await service.list_favorites(user["sub"], page=page, page_size=page_size)
    return ApiResponse.ok(data=result)


@router.post(
    "",
    summary="添加收藏",
    response_model=ApiResponse[FavoriteItem],
)
async def add_favorite(
    req: AddFavoriteRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FavoriteItem]:
    """添加商家到收藏。"""
    service = FavoriteService(db)
    try:
        result = await service.add_favorite(user["sub"], req.shop_id)
        return ApiResponse.ok(data=result, message="收藏成功")
    except AppError as e:
        raise HTTPException(status_code=e.code, detail=e.message)


@router.delete(
    "/{shop_id}",
    summary="移除收藏",
    response_model=ApiResponse[None],
)
async def remove_favorite(
    shop_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    """从收藏中移除指定商家。"""
    service = FavoriteService(db)
    try:
        await service.remove_favorite(user["sub"], shop_id)
        return ApiResponse.ok(message="移除收藏成功")
    except AppError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
