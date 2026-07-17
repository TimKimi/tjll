"""店铺相关 Pydantic 模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Category(BaseModel):
    """店铺分类。"""

    alias: str
    title: str


class Coordinates(BaseModel):
    """经纬度坐标。"""

    latitude: float | None = None
    longitude: float | None = None


class Location(BaseModel):
    """地址信息。"""

    address1: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    display_address: list[str] = []


class BusinessBase(BaseModel):
    """店铺基础字段。"""

    id: str = Field(..., description="店铺 ID")
    name: str = Field(..., description="店铺名称")
    image_url: str | None = None
    rating: float = 0.0
    review_count: int = 0
    price: str | None = None
    categories: list[Category] = []
    location: Location | None = None
    coordinates: Coordinates | None = None
    display_phone: str = ""


class BusinessDetail(BusinessBase):
    """店铺详情。"""

    alias: str = ""
    is_closed: bool = False
    url: str | None = None
    phone: str = ""
    transactions: list[str] = []
    photos: list[str] = []
    hours: Any = None


class BusinessListQuery(BaseModel):
    """店铺列表查询参数。"""

    keyword: str | None = Field(default=None, description="搜索关键词")
    category: str | None = Field(default=None, description="分类别名")
    location: str | None = Field(default=None, description="城市/地区")
    latitude: float | None = None
    longitude: float | None = None
    sort_by: str = Field(
        default="rating", description="排序方式：rating/review_count/distance"
    )
    price: str | None = Field(default=None, description="价格区间，如 1,2,3")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=50)
