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
