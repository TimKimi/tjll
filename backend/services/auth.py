"""认证业务逻辑层：注册、登录、退出、密码找回。"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.core.email import send_email
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

logger = logging.getLogger("backend.services.auth")


def _hash_token(token: str) -> str:
    """对重置令牌做 SHA-256 哈希，用于数据库比对。"""
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    """认证服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, req: RegisterRequest) -> TokenResponse:
        """用户注册。"""
        existing = await self._find_by_username(req.username)
        if existing:
            raise AppError("用户名已存在", code=409)

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
        logger.info("用户注册成功 id=%s username=%s", user.id, user.username)
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
        """用户登录。"""
        user = await self._find_by_username(req.username)
        if not user or not verify_password(req.password, user.password_hash):
            logger.warning("登录失败 username=%s", req.username)
            raise AppError("用户名或密码错误", code=401)

        token = create_token({"sub": user.id, "username": user.username})
        user.is_online = True
        await self.db.commit()

        logger.info("登录成功 id=%s username=%s", user.id, user.username)
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
            logger.info("退出登录 id=%s", user_id)

    async def forgot_password(self, email: str) -> None:
        """发送密码重置邮件。

        无论邮箱是否存在都返回成功，防止邮箱枚举。
        """
        result = await self.db.execute(select(AppUser).where(AppUser.email == email))
        user = result.scalar_one_or_none()

        if not user:
            logger.info("密码找回请求：邮箱不存在 email=%s", email)
            return

        # 生成重置令牌
        raw_token = uuid.uuid4().hex + uuid.uuid4().hex
        user.reset_token = _hash_token(raw_token)
        user.reset_token_exp = datetime.now(timezone.utc).replace(
            tzinfo=None
        ) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        await self.db.commit()

        base_url = (
            settings.APP_BASE_URL or f"http://{settings.APP_HOST}:{settings.APP_PORT}"
        )
        reset_link = f"{base_url}/reset-password?token={raw_token}"
        html = f"""
        <h2>密码重置</h2>
        <p>您好 {user.username}，</p>
        <p>请点击以下链接重置您的密码（{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} 分钟内有效）：</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>如果这不是您本人操作，请忽略此邮件。</p>
        """

        send_email(to=email, subject="密码重置 - TJLL", html=html)
        logger.info("密码重置邮件已发送 id=%s email=%s", user.id, email)

    async def reset_password(self, token: str, new_password: str) -> None:
        """使用重置令牌更新密码。"""
        token_hash = _hash_token(token)

        result = await self.db.execute(
            select(AppUser).where(AppUser.reset_token == token_hash)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise AppError("重置链接无效或已使用", code=400)

        if user.reset_token_exp and user.reset_token_exp < datetime.now(
            timezone.utc
        ).replace(tzinfo=None):
            user.reset_token = None
            user.reset_token_exp = None
            await self.db.commit()
            raise AppError("重置链接已过期", code=400)

        # 更新密码，清除 token
        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_exp = None
        await self.db.commit()

        logger.info("密码重置成功 id=%s", user.id)

    async def _find_by_username(self, username: str) -> AppUser | None:
        result = await self.db.execute(
            select(AppUser).where(AppUser.username == username)
        )
        return result.scalar_one_or_none()
