"""用户路由：个人信息获取与更新。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user
from backend.database import get_db
from backend.schemas.common import ApiResponse
from backend.schemas.user import UpdateProfileRequest, UserProfileResponse
from backend.services.user import UserService

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.get(
    "/profile",
    summary="获取用户信息",
    response_model=ApiResponse[UserProfileResponse],
)
async def get_profile(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserProfileResponse]:
    """获取当前登录用户的个人信息。"""
    service = UserService(db)
    profile = await service.get_profile(user["sub"])
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ApiResponse.ok(data=profile)


@router.put(
    "/profile",
    summary="更新用户信息",
    response_model=ApiResponse[UserProfileResponse],
)
async def update_profile(
    req: UpdateProfileRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserProfileResponse]:
    """更新当前登录用户的个人信息。"""
    service = UserService(db)
    profile = await service.update_profile(user["sub"], req)
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ApiResponse.ok(data=profile, message="更新成功")
