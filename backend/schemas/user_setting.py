"""用户设置 Pydantic 模型。

设置以 JSON 列存储，新增设置项只需在此文件加字段，DB 无需变更。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserSettingData(BaseModel):
    """用户设置数据（已知 key 的显式定义，后续在此扩展）。"""

    model_config = {"extra": "ignore"}

    insight_create: bool = Field(
        default=False,
        description="是否开启洞察创建",
    )
    insight_use: bool = Field(
        default=False,
        description="是否使用历史洞察",
    )
    # ══════════════════════════════════════════════════
    # 新增设置项在此追加字段，设好默认值即可
    # ══════════════════════════════════════════════════


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
    # ══════════════════════════════════════════════════
    # 新增设置项在此追加 Optional 字段
    # ══════════════════════════════════════════════════


class UserSettingResponse(BaseModel):
    """用户设置响应。"""

    id: str = Field(default="", description="设置记录 ID")
    user_id: str = Field(default="", description="用户 ID")
    settings: UserSettingData = Field(
        default_factory=UserSettingData,
        description="用户配置数据",
    )
    created_at: datetime | None = Field(default=None, description="创建时间")
    updated_at: datetime | None = Field(default=None, description="更新时间")
