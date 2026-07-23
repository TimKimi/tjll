"""认证业务逻辑层：注册、登录、退出、密码找回。"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.core.email import send_email
from backend.core.exceptions import AppError
from backend.core.security import create_token, hash_password, verify_password
from backend.llm import get_section_ids, release_ask_sessions_by_uuid
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
    """对重置令牌做 HMAC-SHA256 哈希，使用 JWT 密钥作为 pepper。

    即使数据库泄露，攻击者也无法逆推原始令牌或伪造令牌。
    """
    return hmac.new(
        settings.JWT_SECRET.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _generate_reset_token(email: str) -> str:
    """生成带邮箱绑定的短密钥。

    20 位随机 hex + 4 位邮箱签名 → 24 位 hex，
    邮箱签名 = HMAC-SHA256(secret, email) 的前 4 位，
    使密钥天然与邮箱绑定，无需额外存储。
    """
    random_part = secrets.token_hex(10)  # 80 bits 熵
    email_tag = hmac.new(
        settings.JWT_SECRET.encode("utf-8"),
        email.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:4]  # 4 hex chars = 16 bits 邮箱签名
    return random_part + email_tag


def _format_token(token: str) -> str:
    """格式化密钥为人类友好的分组显示：ABCD-1234-EF56-7890-1234"""
    return "-".join(token[i : i + 4] for i in range(0, len(token), 4))


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

        # 获取该用户已有的会话列表，前端用于恢复历史会话
        sections = get_section_ids(uuid=user.id)

        logger.info(
            "登录成功 id=%s username=%s sections=%d",
            user.id,
            user.username,
            len(sections),
        )
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
            sections=sections,
        )

    async def logout(self, user_id: str) -> None:
        """退出登录，标记用户离线。"""
        result = await self.db.execute(select(AppUser).where(AppUser.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_online = False
            await self.db.commit()
            release_ask_sessions_by_uuid(user.id)
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

        # 生成带邮箱签名的短密钥（24 位 hex，分组显示）
        raw_token = _generate_reset_token(user.email)
        user.reset_token = _hash_token(raw_token)
        user.reset_token_exp = datetime.now(timezone.utc).replace(
            tzinfo=None
        ) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        await self.db.commit()

        html = f"""<div style="max-width:480px; margin:0 auto; padding:40px 20px;
     font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif; color:#333;">

    <div style="text-align:center; margin-bottom:32px;">
        <div style="font-size:22px; font-weight:600; color:#111;">重置密码</div>
    </div>

    <p style="font-size:15px; line-height:1.6; margin:0 0 4px 0;">
        你好 <strong>{user.username}</strong>，
    </p>
    <p style="font-size:15px; line-height:1.6; margin:0 0 28px 0;">
        请使用下面的密钥重置你的 TJLL 账户密码，
        该密钥 <strong>{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} 分钟</strong> 内有效。
    </p>

    <div style="background:#f5f7fa; border-radius:8px; padding:20px; text-align:center; margin-bottom:28px;">
        <span style="font-family:'SF Mono','Cascadia Code','Courier New',monospace;
                    font-size:18px; font-weight:700; letter-spacing:2px; color:#111;
                    white-space:nowrap;">
            {_format_token(raw_token)}
        </span>
    </div>

    <p style="font-size:14px; line-height:1.6; color:#888; margin:0 0 4px 0;">
        如果你没有请求重置密码，请忽略此邮件。
    </p>

    <hr style="border:none; border-top:1px solid #eee; margin:32px 0 0 0;">
    <table cellpadding="0" cellspacing="0" style="width:100%; margin-top:12px; font-size:13px;">
        <tr>
            <td style="text-align:left; color:#555;">TJLL</td>
            <td style="text-align:right; color:#aaa;">大众点评 AI 智能助手</td>
        </tr>
    </table>
</div>
"""

        send_email(to=email, subject="密码重置 - TJLL", html=html)
        logger.info("密码重置邮件已发送 id=%s email=%s", user.id, email)

    async def reset_password(self, token: str, new_password: str) -> None:
        """使用重置令牌更新密码。

        token 包含邮箱签名，通过哈希查找自动锁定所属用户。
        支持去格式化（不区分大小写、忽略短横线）。
        """
        # 清理用户输入：去短横线、转小写
        clean_token = token.replace("-", "").lower()
        token_hash = _hash_token(clean_token)

        result = await self.db.execute(
            select(AppUser).where(AppUser.reset_token == token_hash)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise AppError("密钥无效或已使用", code=400)

        if user.reset_token_exp and user.reset_token_exp < datetime.now(
            timezone.utc
        ).replace(tzinfo=None):
            user.reset_token = None
            user.reset_token_exp = None
            await self.db.commit()
            raise AppError("密钥已过期", code=400)

        # 更新密码，清除 token
        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_exp = None
        await self.db.commit()

        logger.info("密码重置成功 id=%s email=%s", user.id, user.email)

    async def _find_by_username(self, username: str) -> AppUser | None:
        result = await self.db.execute(
            select(AppUser).where(AppUser.username == username)
        )
        return result.scalar_one_or_none()
