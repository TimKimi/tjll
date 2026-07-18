"""协作方请求/响应契约（同进程调用，非 HTTP）。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RagSnippet(BaseModel):
    """单条 RAG 片段。"""

    model_config = ConfigDict(extra="ignore")

    content: str = Field(..., description="片段正文")
    metadata: dict[str, Any] = Field(default_factory=dict, description="片段元数据")


class AskRequest(BaseModel):
    """其他后端模块调用 ask() 的入参。

    本阶段仅处理 query + section_id；附件字段可传但忽略。
    """

    model_config = ConfigDict(extra="ignore")

    query: str = Field(..., min_length=1, description="用户问题")
    section_id: str = Field(..., min_length=1, description="会话/分区 ID（历史 key）")
    uuid: str | None = Field(default=None, description="请求关联 ID，原样回传")
    # 占位：后续路由可能分流，当前不处理
    docx: Any | None = None
    doc: Any | None = None
    md: Any | None = None
    pdf: Any | None = None
    images: Any | None = None


class AskResponse(BaseModel):
    """ask() 返回给其他后端模块的结果。"""

    model_config = ConfigDict(extra="ignore")

    query: str
    section_id: str
    uuid: str | None = None
    answer: str = Field(..., description="LLM 回复")
    sources: list[RagSnippet] = Field(
        default_factory=list,
        description="本轮用到的 RAG 片段",
    )
