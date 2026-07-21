"""用户路由：个人信息获取与更新。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user
from backend.core.exceptions import AppError
from backend.database import get_db
from backend.schemas.common import ApiResponse
from backend.schemas.user import (
    AvatarResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)
from backend.services.avatar import AvatarService
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


@router.post(
    "/avatar",
    summary="上传头像",
    response_model=ApiResponse[AvatarResponse],
)
async def upload_avatar(
    avatar: UploadFile = File(..., description="头像图片文件"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AvatarResponse]:
    """上传用户头像（jpg/png/gif, ≤2MB）。"""
    service = AvatarService(db)
    try:
        result = await service.upload_avatar(user["sub"], avatar)
        return ApiResponse.ok(data=result, message="上传成功")
    except AppError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
