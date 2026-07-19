"""认证路由：注册、登录、退出。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user
from backend.core.exceptions import AppError
from backend.database import get_db
from backend.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from backend.schemas.common import ApiResponse
from backend.services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post(
    "/register",
    summary="用户注册",
    response_model=ApiResponse[TokenResponse],
    status_code=201,
)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """新用户注册，返回 token 和用户信息。"""
    service = AuthService(db)
    try:
        result = await service.register(req)
        return ApiResponse.ok(data=result, message="注册成功")
    except AppError as e:
        raise HTTPException(status_code=e.code, detail=e.message)


@router.post(
    "/login",
    summary="用户登录",
    response_model=ApiResponse[TokenResponse],
)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """用户名密码登录，返回 token 和用户信息。"""
    service = AuthService(db)
    try:
        result = await service.login(req)
        return ApiResponse.ok(data=result, message="登录成功")
    except AppError as e:
        raise HTTPException(status_code=e.code, detail=e.message)


@router.post(
    "/admin/login",
    summary="管理员登录",
    response_model=ApiResponse[TokenResponse],
)
async def admin_login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """管理员登录，需使用 admin 账号。"""
    service = AuthService(db)
    try:
        result = await service.login(req)
        if result.user.role != "admin":
            raise HTTPException(status_code=403, detail="权限不足")
        return ApiResponse.ok(data=result, message="登录成功")
    except AppError as e:
        raise HTTPException(status_code=e.code, detail=e.message)


@router.post(
    "/logout",
    summary="退出登录",
    response_model=ApiResponse[None],
)
async def logout(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    """退出登录，清除在线状态。"""
    service = AuthService(db)
    await service.logout(user["sub"])
    return ApiResponse.ok(message="退出成功")
