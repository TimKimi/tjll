"""用户路由：个人信息、用户设置。

profile 和 settings 均通过泛型 CRUD 工厂注册，保持端点不变。
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.paths import PROJECT_ROOT
from backend.core.crud import SingletonConfig, register_singleton_routes
from backend.core.dependencies import get_current_user
from backend.core.exceptions import AppError
from backend.database import get_db
from backend.llm import (
    delete_all_insights,
    delete_user_insight,
    get_user_insight,
    update_user_insight_attrs,
)
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

logger = logging.getLogger("backend.routers.user")
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
        summary_get="获取用户信息",
        summary_update="更新用户信息",
        error_not_found="用户不存在",
    ),
)

# ── Settings（flat 模式，每个设置项独立字段）───────────────
register_singleton_routes(
    router=router,
    config=SingletonConfig(
        model=UserSetting,
        response_schema=UserSettingResponse,
        update_schema=UserSettingUpdateRequest,
        owner_field="user_id",
        owner_id_from="sub",
        data_mode="flat",
        default_factory=lambda: {"insight_create": False, "insight_use": False},
        prefix="/settings",
        summary_get="获取用户配置",
        summary_update="更新用户配置",
        summary_reset="重置用户配置",
        error_not_found="配置不存在",
        reset=True,
    ),
)

# ── 注销账号 ──────────────────────────────────────────────


async def _cleanup_user_resources(user: AppUser, db: AsyncSession) -> None:
    """注销账号前清理用户关联的文件资源。"""
    # ── 1. 删除头像文件 ───────────────────────────────────
    if user.avatar:
        avatar_filename = Path(user.avatar).name
        avatar_path = PROJECT_ROOT / "static" / "avatars" / avatar_filename
        try:
            if avatar_path.exists():
                avatar_path.unlink()
                logger.info("已删除头像文件: %s", avatar_path)
        except OSError as e:
            logger.warning("删除头像文件失败: %s, %s", avatar_path, e)

    # ── 2. 删除用户上传的附件目录 ─────────────────────────
    if user.username:
        user_file_dir = PROJECT_ROOT / "static" / "file" / user.username
        try:
            if user_file_dir.exists():
                shutil.rmtree(user_file_dir)
                logger.info("已删除用户附件目录: %s", user_file_dir)
        except OSError as e:
            logger.warning("删除用户附件目录失败: %s, %s", user_file_dir, e)


register_singleton_routes(
    router=router,
    config=SingletonConfig(
        model=AppUser,
        response_schema=UserProfileResponse,
        owner_field="id",
        owner_id_from="sub",
        data_mode="flat",
        prefix="/account",
        summary_delete="注销账号",
        description_delete="删除当前用户账号及所有关联数据（设置、收藏、头像、附件等）",
        error_not_found="用户不存在",
        # 只注册 DELETE，不要 GET/PUT/reset
        get=False,
        update=False,
        reset=False,
        delete=True,
        on_delete=_cleanup_user_resources,
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


# ═══════════════════════════════════════════════════════════
# 用户画像
# ═══════════════════════════════════════════════════════════


@router.get(
    "/insight",
    summary="获取用户画像",
    response_model=ApiResponse[dict],
)
async def get_user_insight_route(
    user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    """获取当前用户的画像属性字典。"""
    data = get_user_insight(uuid=user["sub"])
    return ApiResponse.ok(data=data)


@router.put(
    "/insight",
    summary="更新用户画像",
    response_model=ApiResponse,
)
async def update_user_insight_route(
    body: dict[str, Any],
    user: dict = Depends(get_current_user),
) -> ApiResponse:
    """更新用户画像属性（全量替换）。传入 ``{key: value, ...}``。"""
    ok = update_user_insight_attrs(uuid=user["sub"], attrs=body)
    return ApiResponse.ok(message="画像已更新" if ok else "更新失败")


@router.delete(
    "/insight",
    summary="删除用户画像",
    response_model=ApiResponse,
)
async def delete_user_insight_route(
    user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除当前用户的全部画像属性。"""
    ok = delete_user_insight(uuid=user["sub"])
    return ApiResponse.ok(message="画像已删除" if ok else "删除失败")


@router.delete(
    "/insights",
    summary="删除所有画像数据（含各会话）",
    response_model=ApiResponse,
)
async def delete_all_insights_route(
    user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除当前用户所有画像数据（包含各会话的画像）。"""
    ok = delete_all_insights(uuid=user["sub"])
    return ApiResponse.ok(message="所有画像已删除" if ok else "删除失败")
