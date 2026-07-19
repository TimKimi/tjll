"""Auth 相关 Pydantic 请求/响应模型。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """用户角色。"""

    USER = "user"
    ADMIN = "admin"


class RegisterRequest(BaseModel):
    """用户注册请求。"""

    username: str = Field(..., min_length=2, max_length=16, description="用户名")
    password: str = Field(..., min_length=8, description="密码")
    email: str | None = Field(default=None, description="邮箱")


class LoginRequest(BaseModel):
    """用户登录请求。"""

    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")
    remember: bool = Field(default=False, description="是否记住我")


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求。"""

    refresh_token: str = Field(..., min_length=1, description="刷新令牌")


class UserInfo(BaseModel):
    """用户基本信息（登录响应 + 其他接口通用）。"""

    id: str
    username: str
    avatar: str = ""
    is_online: bool = True
    email: str = ""
    bio: str = ""
    register_time: datetime | None = None
    role: UserRole = UserRole.USER


class TokenResponse(BaseModel):
    """登录/刷新 Token 响应。"""

    token: str = Field(..., min_length=1, description="JWT")
    user: UserInfo
