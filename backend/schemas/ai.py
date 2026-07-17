"""AI 助手相关 Pydantic 模型。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ChatRole(str, Enum):
    """消息角色。"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """单条聊天消息。"""

    role: ChatRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """发送对话请求。"""

    message: str = Field(..., description="用户输入的消息")
    conversation_id: str | None = Field(
        default=None, description="会话 ID，不传则新建会话"
    )
    stream: bool = Field(default=False, description="是否流式返回")


class ChatResponse(BaseModel):
    """对话响应。"""

    reply: str = Field(..., description="AI 回复内容")
    conversation_id: str = Field(..., description="会话 ID")


class RecommendRequest(BaseModel):
    """AI 推荐餐厅请求。"""

    location: str | None = Field(default=None, description="地区")
    cuisine: str | None = Field(default=None, description="菜系/口味")
    budget: str | None = Field(default=None, description="预算")
    occasion: str | None = Field(default=None, description="场景，如约会、聚餐")
    latitude: float | None = None
    longitude: float | None = None


class RecommendItem(BaseModel):
    """推荐结果项。"""

    business_id: str
    name: str
    reason: str = Field(..., description="推荐理由")


class RecommendResponse(BaseModel):
    """AI 推荐响应。"""

    recommendations: list[RecommendItem]
    summary: str = Field(..., description="AI 总结说明")


class ReviewSummaryRequest(BaseModel):
    """评论总结请求。"""

    business_id: str = Field(..., description="店铺 ID")


class ReviewSummaryResponse(BaseModel):
    """评论总结响应。"""

    business_id: str
    business_name: str
    pros: list[str] = Field(..., description="好评关键词")
    cons: list[str] = Field(..., description="差评关键词")
    summary: str = Field(..., description="整体总结")


class GenerateReviewRequest(BaseModel):
    """AI 生成点评请求。"""

    business_id: str = Field(..., description="店铺 ID")
    rating: int = Field(default=5, ge=1, le=5, description="评分")
    keywords: list[str] = Field(default=[], description="关键词")
    style: str = Field(default="normal", description="风格：normal/funny/professional")


class GenerateReviewResponse(BaseModel):
    """AI 生成点评响应。"""

    content: str = Field(..., description="生成的点评内容")
