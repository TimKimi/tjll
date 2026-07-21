"""Admin 路由：管理员信息、用户管理。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user
from backend.database import get_db
from backend.schemas.admin import AdminProfileResponse, AdminUserItem
from backend.schemas.common import ApiResponse, PaginatedData
from backend.services.admin import AdminService

router = APIRouter(prefix="/api/admin", tags=["管理后台"])


@router.get(
    "/profile",
    summary="获取管理员信息",
    response_model=ApiResponse[AdminProfileResponse],
)
async def get_admin_profile(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminProfileResponse]:
    """获取当前登录管理员的信息。"""
    service = AdminService(db)
    profile = await service.get_admin_profile(user["sub"])
    if not profile:
        raise HTTPException(status_code=403, detail="权限不足")
    return ApiResponse.ok(data=profile)


@router.get(
    "/users",
    summary="获取所有用户列表",
    response_model=ApiResponse[PaginatedData[AdminUserItem]],
)
async def list_users(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    keyword: str | None = Query(default=None, description="搜索关键词（用户名）"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedData[AdminUserItem]]:
    """管理员获取所有用户列表（分页，支持关键词搜索）。"""
    # 先校验是否为管理员
    service = AdminService(db)
    profile = await service.get_admin_profile(user["sub"])
    if not profile:
        raise HTTPException(status_code=403, detail="权限不足")

    result = await service.list_users(
        page=page,
        page_size=page_size,
        keyword=keyword,
    )
    return ApiResponse.ok(data=result)
