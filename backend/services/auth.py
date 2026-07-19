"""认证业务逻辑层：注册、登录、退出。"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import AppError
from backend.core.security import create_token, hash_password, verify_password
from backend.models.app_user import AppUser
from backend.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserInfo,
    UserRole,
)


class AuthService:
    """认证服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, req: RegisterRequest) -> TokenResponse:
        """用户注册。

        Raises:
            AppError: 用户名已存在。
        """
        existing = await self._find_by_username(req.username)
        if existing:
            raise AppError("用户名已存在", code=400)

        user = AppUser(
            id=uuid.uuid4().hex[:22],
            username=req.username,
            password_hash=hash_password(req.password),
            email=req.email,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        token = create_token({"sub": user.id, "username": user.username})
        return TokenResponse(
            token=token,
            user=UserInfo(
                id=user.id,
                username=user.username,
                avatar=user.avatar or "",
                email=user.email,
                register_time=user.register_time,
            ),
        )

    async def login(self, req: LoginRequest) -> TokenResponse:
        """用户登录。

        Raises:
            AppError: 用户不存在或密码错误。
        """
        user = await self._find_by_username(req.username)
        if not user:
            raise AppError("用户不存在", code=404)

        if not verify_password(req.password, user.password_hash):
            raise AppError("密码错误", code=401)

        token = create_token({"sub": user.id, "username": user.username})

        user.is_online = True
        await self.db.commit()

        return TokenResponse(
            token=token,
            user=UserInfo(
                id=user.id,
                username=user.username,
                avatar=user.avatar or "",
                is_online=True,
                email=user.email,
                bio=user.bio or "",
                register_time=user.register_time,
                role=UserRole.ADMIN if user.role == "admin" else UserRole.USER,
            ),
        )

    async def logout(self, user_id: str) -> None:
        """退出登录，标记用户离线。"""
        result = await self.db.execute(select(AppUser).where(AppUser.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_online = False
            await self.db.commit()

    async def _find_by_username(self, username: str) -> AppUser | None:
        result = await self.db.execute(
            select(AppUser).where(AppUser.username == username)
        )
        return result.scalar_one_or_none()
