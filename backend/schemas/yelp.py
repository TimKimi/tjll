"""Yelp API 相关的 Pydantic 模型。

分层设计：
  - Yelp*        → 与 Yelp API 响应结构一一对应（解析用）
  - Stored*      → 本地持久化格式（存库用）
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ============================================================
# 一、Yelp API 响应模型（与 API.md 对齐）
# ============================================================


class YelpCategory(BaseModel):
    """商家分类。"""

    alias: str
    title: str


class YelpCoordinates(BaseModel):
    """经纬度坐标。"""

    latitude: float
    longitude: float


class YelpOpenHour(BaseModel):
    """营业时间中的某一天时段。"""

    day: int = Field(..., description="星期几，0=周日")
    start: str = Field(..., description="开始时间，24h 格式如 0900")
    end: str = Field(..., description="结束时间，24h 格式如 2100")
    is_overnight: bool = Field(..., description="是否跨午夜")


class YelpBusinessHours(BaseModel):
    """营业时间。"""

    open: list[YelpOpenHour] = []
    hours_type: str = "REGULAR"
    is_open_now: bool = False


class YelpLocation(BaseModel):
    """地址信息。"""

    address1: str | None = None
    address2: str | None = None
    address3: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    display_address: list[str] = []


class YelpBusiness(BaseModel):
    """商家基本／详细信息（Search + Details 共有字段的并集）。"""

    # ── 核心标识 ──
    id: str = Field(..., description="Yelp 商家 ID，22 字符")
    alias: str
    name: str

    # ── 基础信息 ──
    image_url: str | None = None
    is_closed: bool = False
    url: str | None = None
    review_count: int = 0
    rating: float = 0.0
    price: str | None = None

    # ── 分类 ──
    categories: list[YelpCategory] = []

    # ── 位置 ──
    coordinates: YelpCoordinates | None = None
    location: YelpLocation | None = None

    # ── 联系方式 ──
    phone: str = ""
    display_phone: str = ""

    # ── 营业 ──
    hours: YelpBusinessHours | None = Field(None, alias="business_hours")
    special_hours: list[dict] | None = None

    @field_validator("hours", mode="before")
    @classmethod
    def _normalize_hours(cls, v: object) -> object:
        """Search 返回 list，Details 返回单对象，统一取第一个。"""
        if isinstance(v, list):
            return v[0] if v else None
        return v

    # ── 其他 ──
    transactions: list[str] = []
    distance: float | None = None
    is_claimed: bool | None = None
    photos: list[str] = []

    # Details 专属（Premium）
    yelp_menu_url: str | None = None
    attributes: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class YelpBusinessSearchResponse(BaseModel):
    """Business Search 响应。"""

    businesses: list[YelpBusiness]
    total: int
    region: dict = {}


class YelpReviewUser(BaseModel):
    """评论作者。"""

    id: str
    profile_url: str
    image_url: str | None = None
    name: str


class YelpReview(BaseModel):
    """评论。"""

    id: str
    url: str
    text: str
    rating: int
    time_created: str
    user: YelpReviewUser


class YelpReviewsResponse(BaseModel):
    """Reviews 响应。"""

    reviews: list[YelpReview]
    total: int
    possible_languages: list[str] = []


# ============================================================
# 二、本地持久化模型（存库用）
# ============================================================


class StoredBusiness(BaseModel):
    """存入本地的商家完整信息。"""

    # ── 元信息 ──
    stored_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # ── 从 Yelp 拉取的数据 ──
    yelp_id: str = Field(..., alias="id")
    alias: str
    name: str
    image_url: str | None = None
    is_closed: bool = False
    url: str | None = None
    review_count: int = 0
    rating: float = 0.0
    price: str | None = None
    categories: list[YelpCategory] = []
    coordinates: YelpCoordinates | None = None
    location: YelpLocation | None = None
    phone: str = ""
    display_phone: str = ""
    hours: YelpBusinessHours | None = None
    transactions: list[str] = []
    photos: list[str] = []
    yelp_menu_url: str | None = None
    attributes: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}

    @classmethod
    def from_yelp(cls, biz: YelpBusiness) -> "StoredBusiness":
        """从 Yelp API 响应创建本地存储对象。"""
        data = biz.model_dump(by_alias=True)
        return cls(**data)


class StoredReview(BaseModel):
    """存入本地的评论。"""

    # ── 元信息 ──
    stored_at: datetime = Field(default_factory=datetime.now)

    # ── 关联 ──
    business_id: str = Field(..., description="所属商家 Yelp ID")

    # ── 评论内容 ──
    id: str
    url: str
    text: str
    rating: int
    time_created: str
    user: YelpReviewUser

    @classmethod
    def from_yelp(cls, review: YelpReview, business_id: str) -> "StoredReview":
        """从 Yelp API 响应创建本地存储对象。"""
        data = review.model_dump()
        data["business_id"] = business_id
        return cls(**data)
