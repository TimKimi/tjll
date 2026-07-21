"""Admin 相关 Pydantic 请求/响应模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AdminProfileResponse(BaseModel):
    """管理员信息响应。"""

    id: str
    username: str
    avatar: str = ""
    role: str = "admin"


class AdminUserItem(BaseModel):
    """管理员视角的用户列表项。"""

    id: str
    username: str
    email: str = ""
    bio: str = ""
    avatar: str = ""
    is_online: bool = True
    register_time: datetime | None = None
    role: str = "user"


class AdminUserListQuery(BaseModel):
    """管理员用户列表查询参数。"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")
    keyword: str | None = Field(default=None, description="搜索关键词（用户名）")
