"""AI / LLM 协作模型（Python 门面，非 HTTP DTO）。

外部模块请 ``from backend.schemas.llm import ...`` 或 ``from backend.llm import ...``。
结构体禁止以 Request/Response 结尾；路由层由对接方自行封装。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ==========================================================================


# 1. ai对话
#    user，string， section——id
#       func（user，string， section）--》stream（str）
# ## 会话id
#       1. 数据库
#       2. redis  func（user）--》list（section-id）
# 2. 历史
#       1. func（section-id）--》list（message）
#


# ==============================================================================


class RagSnippet(BaseModel):
    """单条 RAG 片段：正文 + 索引元字段（不含 embedding）。"""

    content: str = Field(..., description="片段正文（text）")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="索引全字段（除 embedding）及 score / rerank_score 等",
    )


class HistoryMessage(BaseModel):
    """会话历史单条（对外不含 search_query）。"""

    role: Literal["user", "assistant", "system"] = Field(..., description="角色")
    content: str = Field(..., description="消息正文")
    filename: str | None = Field(
        default=None,
        description="用户轮：关联文件名，可为空",
    )
    insight_create: bool | None = Field(
        default=None,
        description="用户轮：该次是否要求创建洞察；助手/系统为 null",
    )
    insight_use: bool | None = Field(
        default=None,
        description="用户轮：该次是否使用洞察；助手/系统为 null",
    )
    sources: list[RagSnippet] | None = Field(
        default=None,
        description="助手轮：本轮回复使用的参考资料",
    )


class AskParams(BaseModel):
    """ask() 入参。"""

    query: str = Field(..., min_length=1, description="用户问题")
    section_id: str = Field(..., min_length=1, description="会话/分区 ID（历史 key）")
    uuid: str = Field(
        ...,
        min_length=1,
        description="用户/请求关联 ID（与 section_id 共同作为历史 key）",
    )
    docx: list[str] | None = Field(
        default=None,
        description="文件路径列表；无附件为 null。路径如 ./backend/.../name.docx",
    )
    doc: list[str] | None = Field(default=None, description="同上")
    txt: list[str] | None = Field(default=None, description="同上")
    md: list[str] | None = Field(default=None, description="同上")
    pdf: list[str] | None = Field(default=None, description="同上")
    images: list[str] | None = Field(
        default=None,
        description="图片路径列表；无附件为 null",
    )
    insight_create: bool = Field(default=False, description="是否创建洞察")
    insight_use: bool = Field(default=False, description="是否使用洞察")


class AskResult(BaseModel):
    """ask() 完整结果（不含会话历史；历史请用 get_ask_history）。"""

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
        description="当前轮用户请求附带的文件名（逗号拼接路径）",
    )


class AskHistory(BaseModel):
    """完整会话历史（含扩展字段，不含 search_query）。"""

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


class DeleteHistoryResult(BaseModel):
    """按 uuid 删除全部会话历史的结果。"""

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


class AskInterruptQuestion(BaseModel):
    """单道澄清题：option 为 A/B/… → 文案；提交答案后洞察内改为 result。"""

    question: str = Field(..., min_length=1)
    option: dict[str, str] = Field(
        default_factory=dict,
        description='选项映射，如 {"A": "…", "B": "…"}',
    )


class AskInterruptResult(BaseModel):
    """ask() 在 rewrite 打断时返回的问卷（一层封装）。"""

    uuid: str
    section_id: str
    questions: list[AskInterruptQuestion] = Field(default_factory=list)


class AskInterruptAnswerItem(BaseModel):
    """单题答案：result 为选项原文或自定义文本。"""

    question: str = Field(..., min_length=1)
    result: str = Field(..., min_length=1)


class AskInterruptSubmitParams(BaseModel):
    """提交澄清答案；受理后从 rewrite 续跑并返回 AskStream。"""

    uuid: str = Field(..., min_length=1)
    section_id: str = Field(..., min_length=1)
    answers: list[AskInterruptAnswerItem] = Field(default_factory=list)
