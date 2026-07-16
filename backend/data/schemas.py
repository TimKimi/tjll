"""Yelp 学术数据集 JSONL 的 Pydantic 模型。

数据来源: https://www.yelp.com/dataset
每个 JSONL 文件每行一个 JSON 对象。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ============================================================
# 一、原始 JSONL 行模型（与数据集文件一一对应）
# ============================================================


class DatasetBusiness(BaseModel):
    """yelp_academic_dataset_business.json 的每行结构。"""

    business_id: str = Field(..., description="Yelp 商家 ID")
    name: str
    address: str
    city: str
    state: str
    postal_code: str
    latitude: float | None = None
    longitude: float | None = None
    stars: float = 0.0
    review_count: int = 0
    is_open: int = Field(..., description="1=营业, 0=关闭")
    attributes: dict | None = None
    categories: str | None = None  # 逗号分隔的字符串，可能为 null
    hours: dict | None = None  # { "Monday": "8:0-18:30", ... }


class DatasetReview(BaseModel):
    """yelp_academic_dataset_review.json 的每行结构。

    注意：实际 JSON 文件中 stars 是浮点数（如 3.0, 5.0），
    但语义上是整数评分，ORM 中也存为 Integer。
    """

    review_id: str = Field(..., description="Yelp 评论 ID")
    user_id: str
    business_id: str
    stars: float = Field(..., description="评分 1~5，JSON 中为浮点数")
    useful: int = 0
    funny: int = 0
    cool: int = 0
    text: str
    date: str = Field(..., description="评论创建时间")


class DatasetUser(BaseModel):
    """yelp_academic_dataset_user.json 的每行结构。"""

    user_id: str
    name: str
    review_count: int = 0
    yelping_since: str = ""
    useful: int = 0
    funny: int = 0
    cool: int = 0
    elite: str = ""
    friends: str = ""
    fans: int = 0
    average_stars: float = 0.0
    compliment_hot: int = 0
    compliment_more: int = 0
    compliment_profile: int = 0
    compliment_cute: int = 0
    compliment_list: int = 0
    compliment_note: int = 0
    compliment_plain: int = 0
    compliment_cool: int = 0
    compliment_funny: int = 0
    compliment_writer: int = 0
    compliment_photos: int = 0


class DatasetTip(BaseModel):
    """yelp_academic_dataset_tip.json 的每行结构。"""

    user_id: str
    business_id: str
    text: str
    date: str
    compliment_count: int = 0


class DatasetCheckin(BaseModel):
    """yelp_academic_dataset_checkin.json 的每行结构。"""

    business_id: str
    date: str  # 逗号分隔的时间戳列表


# ============================================================
# 二、转换后的数据模型（与现有 ORM 模型兼容的中间结构）
# ============================================================


class ConvertedBusiness(BaseModel):
    """从 DatasetBusiness 转换后，准备写入 ORM 的数据。

    字段名和类型与 ORM Business 模型对齐。
    """

    id: str
    alias: str = ""  # 数据集没有 alias，取 name 的 slug
    name: str
    image_url: str | None = None
    is_closed: bool = False
    url: str | None = None
    review_count: int = 0
    rating: float = 0.0
    price: str | None = None
    categories: str | None = None  # JSON 字符串
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None  # JSON 字符串
    phone: str = ""
    display_phone: str = ""
    hours: str | None = None  # JSON 字符串
    transactions: str | None = None  # JSON 字符串
    photos: str | None = None  # JSON 字符串
    yelp_menu_url: str | None = None


class ConvertedReview(BaseModel):
    """从 DatasetReview 转换后，准备写入 ORM 的数据。

    字段名和类型与 ORM Review 模型对齐。
    """

    id: str
    business_id: str
    url: str = ""
    text: str
    rating: int
    time_created: str
    user: str | None = None  # JSON 字符串
