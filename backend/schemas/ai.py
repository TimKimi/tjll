"""AI 对话 HTTP 请求/响应模型。

路由层专属，非 LLM 模块内部 schema。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AskChatRequest(BaseModel):
    """AI 对话请求体。"""

    model_config = {"extra": "ignore"}

    query: str = Field(..., min_length=1, description="用户问题")
    section_id: str = Field(..., min_length=1, description="会话 ID")
    docx: list[str] = Field(
        default_factory=list,
        description="docx 文件路径列表，前端按扩展名分类后传入",
    )
    doc: list[str] = Field(default_factory=list, description="同上")
    txt: list[str] = Field(default_factory=list, description="同上")
    md: list[str] = Field(default_factory=list, description="同上")
    pdf: list[str] = Field(default_factory=list, description="同上")
    images: list[str] = Field(
        default_factory=list,
        description="图片文件路径列表（png/jpg/jpeg/gif/webp）",
    )
    insight_create: bool = Field(default=False, description="是否创建洞察")
    insight_use: bool = Field(default=False, description="是否使用洞察")
    stream: bool = Field(default=True, description="是否流式返回")


class FileUploadResponse(BaseModel):
    """文件上传响应。"""

    filename: str = Field(description="文件名")
    url: str = Field(
        description=(
            "文件路径，格式 ./backend/static/file/{username}/{section_id}/{filename}"
            "，可直接用于 AskParams 的附件字段"
        ),
    )
    size: int = Field(description="文件大小（字节）")
    mime_type: str = Field(description="MIME 类型")


class SectionReviewItem(BaseModel):
    """单个会话的摘要。"""

    section_id: str = Field(description="会话 ID")
    review: str = Field(default="", description="会话摘要文本")


class SectionReviewsResponse(BaseModel):
    """批量会话摘要响应。"""

    reviews: list[SectionReviewItem] = Field(
        default_factory=list,
        description="会话摘要列表",
    )


class InsightItem(BaseModel):
    """单条洞察属性。"""

    key: str = Field(description="属性名")
    value: str = Field(description="属性值")


class SessionDetailResponse(BaseModel):
    """会话详情响应。"""

    facts: list[str] = Field(
        default_factory=list,
        description="会话 facts 列表，按时间顺序",
    )
    review: str = Field(default="", description="会话 review 文本")
    insight: list[InsightItem] = Field(
        default_factory=list,
        description="会话洞察属性列表",
    )
