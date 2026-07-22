"""ask 请求/响应模型。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RagSnippet(BaseModel):
    """单条 RAG 片段：正文 + 索引元字段（不含 embedding）。"""

    model_config = ConfigDict(extra="ignore")

    content: str = Field(..., description="片段正文（text）")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="索引全字段（除 embedding）及 score / rerank_score 等",
    )


class HistoryMessage(BaseModel):
    """会话历史单条（本轮写入前已存在的消息；响应中不含 search_query）。"""

    model_config = ConfigDict(extra="ignore")

    role: Literal["user", "assistant", "system"] = Field(..., description="角色")
    content: str = Field(..., description="消息正文")
    filename: str | None = Field(
        default=None,
        description="用户轮：关联文件名，可为空",
    )
    sources: list[RagSnippet] | None = Field(
        default=None,
        description="助手轮：本轮回复使用的参考资料",
    )


class AskRequest(BaseModel):
    """ask() 入参。附件字段可传，当前忽略。"""

    model_config = ConfigDict(extra="ignore")

    query: str = Field(..., min_length=1, description="用户问题")
    section_id: str = Field(..., min_length=1, description="会话/分区 ID（历史 key）")
    uuid: str = Field(
        ...,
        min_length=1,
        description="用户/请求关联 ID（与 section_id 共同作为历史 key）",
    )
    # 占位：后续路由可能分流，当前不处理
    docx: Any | None = None
    doc: Any | None = None
    md: Any | None = None
    pdf: Any | None = None
    images: Any | None = None
    # 占位：后续可能需要设置项
    insight_create: bool = Field(default=False, description="是否创建洞察")
    insight_use: bool = Field(default=False, description="是否使用洞察")


class AskResponse(BaseModel):
    """ask() 响应。"""

    model_config = ConfigDict(extra="ignore")

    query: str
    section_id: str
    uuid: str
    answer: str = Field(..., description="LLM 回复")
    sources: list[RagSnippet] = Field(
        default_factory=list,
        description="本轮参考资料RAG片段",
    )
    history: list[HistoryMessage] = Field(
        default_factory=list,
        description="已有会话历史（含扩展字段，不含 search_query）",
    )
    query_filename: str = Field(
        default="",
        description="当前轮用户请求附带的文件名；暂为空，后续维护",
    )
