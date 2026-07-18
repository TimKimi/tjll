"""评论相关 Pydantic 模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewUser(BaseModel):
    """评论作者信息。"""

    id: str
    name: str
    profile_url: str = ""
    image_url: str | None = None


class ReviewBase(BaseModel):
    """评论基础字段。"""

    id: str = Field(..., description="评论 ID")
    business_id: str = Field(..., description="所属店铺 ID")
    text: str = Field(..., description="评论内容")
    rating: int = Field(..., description="评分 1-5")
    time_created: str = Field(..., description="创建时间")
    user: ReviewUser | None = None
    url: str = ""
