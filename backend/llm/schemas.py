"""ask / 历史 / 洞察 / interrupt 等协作接口的请求/响应模型。"""

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
    """会话历史单条（对外不含 search_query）。"""

    model_config = ConfigDict(extra="ignore")

    role: Literal["user", "assistant", "system"] = Field(..., description="角色")
    content: str = Field(..., description="消息正文")
    filename: str | None = Field(
        default=None,
        description="用户轮：关联文件名，可为空",
    )
    insight_create: bool | None = Field(
        default=None,
        description="用户轮：该次请求是否要求创建洞察；助手/系统轮为 null",
    )
    insight_use: bool | None = Field(
        default=None,
        description="用户轮：该次请求是否使用洞察；助手/系统轮为 null",
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
    txt: Any | None = None
    md: Any | None = None
    pdf: Any | None = None
    images: Any | None = None
    insight_create: bool = Field(default=False, description="是否创建洞察")
    insight_use: bool = Field(default=False, description="是否使用洞察")


class AskResponse(BaseModel):
    """ask() 响应（不含会话历史；历史请用 get_ask_history）。"""

    model_config = ConfigDict(extra="ignore")

    query: str
    section_id: str
    uuid: str
    answer: str = Field(..., description="LLM 回复")
    sources: list[RagSnippet] = Field(
        default_factory=list,
        description="本轮参考资料RAG片段",
    )
    query_filename: str = Field(
        default="",
        description="当前轮用户请求附带的文件名；暂为空，后续维护",
    )


class HistoryRequest(BaseModel):
    """拉取/删除单个会话历史，或按会话操作洞察的入参。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str = Field(..., min_length=1, description="用户/请求关联 ID")
    section_id: str = Field(..., min_length=1, description="会话/分区 ID")


class HistoryResponse(BaseModel):
    """完整会话历史（含扩展字段，不含 search_query）。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str
    section_id: str
    history: list[HistoryMessage] = Field(default_factory=list)
    insight_create: bool = Field(
        default=False,
        description="末条 user 消息的 insight_create；无 user 消息时为 false",
    )
    insight_use: bool = Field(
        default=False,
        description="末条 user 消息的 insight_use；无 user 消息时为 false",
    )


class UuidRequest(BaseModel):
    """仅 uuid 的通用入参。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str = Field(..., min_length=1, description="用户/请求关联 ID")


class DeleteHistoryByUuidRequest(UuidRequest):
    """按 uuid 删除该用户全部会话历史的入参。"""


class DeleteHistoryResponse(BaseModel):
    """删除历史结果。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str
    section_id: str | None = Field(
        default=None,
        description="单会话删除时回传；按 uuid 全删时为 null",
    )
    deleted_sessions: int = Field(..., description="实际清理的会话数")
    section_ids: list[str] = Field(
        default_factory=list,
        description="被清理的 section_id 列表",
    )


class ReleaseSessionsResponse(BaseModel):
    """按 uuid 释放会话池 / 登出清池的结果。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str
    released_sessions: int = Field(..., description="释放的会话槽数量")
    section_ids: list[str] = Field(
        default_factory=list,
        description="被释放的 section_id 列表",
    )


class DeleteInsightResponse(BaseModel):
    """删除洞察结果（占位）。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str
    section_id: str | None = Field(
        default=None,
        description="单会话删除时回传；否则 null",
    )
    deleted: bool = Field(..., description="是否视为删除成功（占位）")
    scope: Literal["user", "section", "all"] = Field(
        ...,
        description="删除范围：用户总体 / 单会话 / 全部",
    )


class UserInsightResponse(BaseModel):
    """用户总体洞察属性查询。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str
    attrs: dict[str, str] = Field(default_factory=dict)


class SectionInsightResponse(BaseModel):
    """会话洞察属性查询（日后可动态合并父类属性）。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str
    section_id: str
    attrs: dict[str, str] = Field(default_factory=dict)
    filenames: list[str] = Field(default_factory=list)


class UpdateUserInsightAttrsRequest(BaseModel):
    """批量更新用户总体洞察属性。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str = Field(..., min_length=1)
    attrs: dict[str, Any] = Field(default_factory=dict)


class UpdateSectionInsightAttrsRequest(BaseModel):
    """批量更新会话洞察属性。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str = Field(..., min_length=1)
    section_id: str = Field(..., min_length=1)
    attrs: dict[str, Any] = Field(default_factory=dict)


class SectionFactsResponse(BaseModel):
    """会话 facts 读取。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str
    section_id: str
    facts: list[str] = Field(default_factory=list)


class UpdateSectionFactsRequest(BaseModel):
    """会话 facts 写入（语义对齐 SectionInsight.add_facts）。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str = Field(..., min_length=1)
    section_id: str = Field(..., min_length=1)
    items: list[str] = Field(default_factory=list)
    start: int | None = Field(
        default=None,
        description="1-based：从第 start 条起截断再追加；None 表示仅追加",
    )


class SectionReviewResponse(BaseModel):
    """会话 review 读取。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str
    section_id: str
    review: str = ""


class SetSectionReviewRequest(BaseModel):
    """会话 review 覆盖写入。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str = Field(..., min_length=1)
    section_id: str = Field(..., min_length=1)
    text: str = ""


class LoadSectionDocumentRequest(BaseModel):
    """加载并处理会话文档。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str = Field(..., min_length=1)
    section_id: str = Field(..., min_length=1)
    file_path: str = Field(..., min_length=1, description="相对 tjll 仓库根的路径")


class LoadSectionDocumentResponse(BaseModel):
    """文档处理结果（占位）。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str
    section_id: str
    source_file: str = ""
    chunks: int = 0
    filenames: list[str] = Field(default_factory=list)


class AskInterruptCreateRequest(BaseModel):
    """创建 ask interrupt 澄清问卷。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str = Field(..., min_length=1)
    section_id: str = Field(..., min_length=1)
    query: str | None = Field(default=None, description="可选上下文问题")


class AskInterruptQuestion(BaseModel):
    """单道澄清题：选项最后一项约定为「其他」。"""

    model_config = ConfigDict(extra="ignore")

    id: str
    prompt: str
    options: list[str] = Field(default_factory=list)


class AskInterruptCreateResponse(BaseModel):
    """澄清问卷创建结果（占位可返回空 questions）。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str
    section_id: str
    interrupt_id: str = ""
    questions: list[AskInterruptQuestion] = Field(default_factory=list)


class AskInterruptAnswerItem(BaseModel):
    """单题答案：answer 为选项原文或自定义文本（非序号）。"""

    model_config = ConfigDict(extra="ignore")

    question_id: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)


class AskInterruptSubmitRequest(BaseModel):
    """提交澄清问卷答案。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str = Field(..., min_length=1)
    section_id: str = Field(..., min_length=1)
    interrupt_id: str = Field(..., min_length=1)
    answers: list[AskInterruptAnswerItem] = Field(default_factory=list)


class AskInterruptSubmitResponse(BaseModel):
    """澄清答案受理结果（占位）。"""

    model_config = ConfigDict(extra="ignore")

    uuid: str
    section_id: str
    interrupt_id: str
    accepted: bool = False
