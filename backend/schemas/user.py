"""User 相关 Pydantic 请求/响应模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserProfileResponse(BaseModel):
    """用户信息响应。"""

    id: str
    username: str
    avatar: str = ""
    is_online: bool = True
    email: str = ""
    bio: str = ""
    register_time: datetime | None = None


class UpdateProfileRequest(BaseModel):
    """更新用户信息请求（全部选填）。"""

    username: str | None = Field(default=None, min_length=2, max_length=16)
    email: EmailStr | None = None
    bio: str | None = Field(default=None, max_length=500)
