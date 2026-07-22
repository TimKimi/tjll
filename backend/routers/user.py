"""用户路由：个人信息、用户设置。

profile 和 settings 均通过泛型 CRUD 工厂注册，保持端点不变。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.crud import SingletonConfig, register_singleton_routes
from backend.core.dependencies import get_current_user
from backend.core.exceptions import AppError
from backend.database import get_db
from backend.models.app_user import AppUser
from backend.models.user_setting import UserSetting
from backend.schemas.common import ApiResponse
from backend.schemas.user import (
    AvatarResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)
from backend.schemas.user_setting import (
    UserSettingResponse,
    UserSettingUpdateRequest,
)
from backend.services.avatar import AvatarService

router = APIRouter(prefix="/api/user", tags=["用户"])

# ── Profile（flat 模式，兼容现有前端端点）──────────────────
register_singleton_routes(
    router=router,
    config=SingletonConfig(
        model=AppUser,
        response_schema=UserProfileResponse,
        update_schema=UpdateProfileRequest,
        owner_field="id",  # AppUser.id == JWT.sub
        owner_id_from="sub",
        data_mode="flat",
        prefix="/profile",
        tags=["用户"],
        summary_get="获取用户信息",
        summary_update="更新用户信息",
        error_not_found="用户不存在",
    ),
)

# ── Settings（json 模式）───────────────────────────────────
register_singleton_routes(
    router=router,
    config=SingletonConfig(
        model=UserSetting,
        response_schema=UserSettingResponse,
        update_schema=UserSettingUpdateRequest,
        owner_field="user_id",
        owner_id_from="sub",
        data_mode="json",
        json_column="settings",
        default_factory=lambda: {"insight_create": False, "insight_use": False},
        prefix="/settings",
        tags=["用户"],
        summary_get="获取用户配置",
        summary_update="更新用户配置",
        summary_reset="重置用户配置",
        error_not_found="配置不存在",
        reset=True,
    ),
)


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
