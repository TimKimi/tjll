"""用户设置 Pydantic 模型。

每个设置项都是独立字段，新增设置在模型和 schema 同步加字段即可。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserSettingResponse(BaseModel):
    """用户设置响应。"""

    id: str = Field(default="", description="设置记录 ID")
    user_id: str = Field(default="", description="用户 ID")
    insight_create: bool = Field(
        default=False,
        description="是否开启洞察创建",
    )
    insight_use: bool = Field(
        default=False,
        description="是否使用历史洞察",
    )
    created_at: datetime | None = Field(default=None, description="创建时间")
    updated_at: datetime | None = Field(default=None, description="更新时间")


class UserSettingUpdateRequest(BaseModel):
    """更新用户设置的请求（全部可选，仅传要改的字段）。"""

    model_config = {"extra": "ignore"}

    insight_create: bool | None = Field(
        default=None,
        description="是否开启洞察创建",
    )
    insight_use: bool | None = Field(
        default=None,
        description="是否使用历史洞察",
    )
