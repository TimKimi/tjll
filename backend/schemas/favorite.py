"""Favorite 相关 Pydantic 请求/响应模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AddFavoriteRequest(BaseModel):
    """添加收藏请求。"""

    shop_id: str = Field(..., min_length=1, description="商家 ID")
    source: str = Field(default="db", description="数据来源：db / yelp")


class FavoriteItem(BaseModel):
    """收藏项（含店铺摘要信息）。"""

    id: str = Field(..., description="收藏记录 ID")
    shop_id: str = Field(..., description="商家 ID")
    source: str = Field(default="db", description="数据来源：db / yelp")
    name: str = Field(default="", description="商家名称")
    image_url: str = Field(default="", description="商家封面图 URL")
    rating: float = Field(default=0.0, description="评分")
    price: str = Field(default="", description="价格等级")
    address: str = Field(default="", description="地址")
    category: str = Field(default="", description="分类名称")
    created_at: datetime = Field(description="收藏时间")
