"""Admin 路由：管理员信息、用户管理。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user
from backend.core.exceptions import AppError
from backend.database import get_db
from backend.schemas.admin import (
    AdminProfileResponse,
    AdminUserItem,
    UpdateRoleRequest,
)
from backend.schemas.common import ApiResponse, PaginatedData
from backend.services.admin import AdminService

logger = logging.getLogger("backend.routers.admin")
router = APIRouter(prefix="/api/admin", tags=["管理后台"])


async def _ensure_admin(user: dict, db: AsyncSession) -> AdminService:
    """校验当前用户是否为管理员，返回 AdminService 实例。"""
    service = AdminService(db)
    profile = await service.get_admin_profile(user["sub"])
    if not profile:
        raise HTTPException(status_code=403, detail="权限不足")
    return service


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
    service = await _ensure_admin(user, db)
    profile = await service.get_admin_profile(user["sub"])
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
    service = await _ensure_admin(user, db)
    result = await service.list_users(
        page=page,
        page_size=page_size,
        keyword=keyword,
    )
    return ApiResponse.ok(data=result)


@router.put(
    "/users/{user_id}/role",
    summary="修改用户角色",
    response_model=ApiResponse[AdminUserItem],
)
async def update_user_role(
    user_id: str,
    req: UpdateRoleRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminUserItem]:
    """管理员修改指定用户的角色。"""
    service = await _ensure_admin(user, db)
    try:
        result = await service.change_role(user["sub"], user_id, req.role)
        logger.info(
            "角色变更成功 admin=%s target=%s role=%s", user["sub"], user_id, req.role
        )
        return ApiResponse.ok(data=result, message="角色更新成功")
    except AppError as e:
        raise HTTPException(status_code=e.code, detail=e.message)


@router.delete(
    "/users/{user_id}",
    summary="删除用户",
    response_model=ApiResponse[None],
)
async def delete_user(
    user_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    """管理员删除指定用户。"""
    service = await _ensure_admin(user, db)
    try:
        await service.delete_user(user["sub"], user_id)
        logger.warning("用户删除成功 admin=%s target=%s", user["sub"], user_id)
        return ApiResponse.ok(message="用户已删除")
    except AppError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
