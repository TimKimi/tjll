"""洞察维护用 Prompt。"""

from langchain_core.prompts import ChatPromptTemplate

MAINTAIN_REVIEW_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你维护会话 review 摘要。根据已有 review 与最近对话，用工具写入新的 review。\n"
            "规则：简洁中文；总字数严格不超过 150 字；只调用 set_section_review 一次；无新信息可不改。",
        ),
        (
            "human",
            "当前 review：\n{review}\n\n最近对话：\n{history_text}\n\n请更新 review。",
        ),
    ]
)

MAINTAIN_FACTS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你维护会话 facts 时间线。可多次调用 add_section_facts。\n"
            "规则：每条事实不超过 20 字；客观陈述；互斥不拆条；顺序即时间顺序；"
            "无新事实可不调用工具。",
        ),
        (
            "human",
            "当前 facts：\n{facts_text}\n\n最近对话：\n{history_text}\n\n请维护 facts。",
        ),
    ]
)

MAINTAIN_SECTION_ATTRS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你维护本会话短属性（人数/偏好/预算/忌口/场景等）。必须调用 "
            "batch_add_section_insight_attrs；对话里用户明确说过的偏好要写入。\n"
            "规则：键值尽量短；互斥覆盖同名键；无依据才可不加。",
        ),
        (
            "human",
            "当前会话属性：\n{attrs_text}\n\n最近对话：\n{history_text}\n\n"
            "请从对话提取并追加会话属性。",
        ),
    ]
)

MAINTAIN_USER_ATTRS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你根据会话属性，向用户级画像追加互斥短属性。调用 batch_add_insight_attrs。\n"
            "规则：键值短小；无则不加；不要编造。",
        ),
        (
            "human",
            "当前用户属性：\n{user_attrs_text}\n\n会话属性：\n{section_attrs_text}\n\n"
            "相关对话：\n{history_text}\n\n请按需追加用户属性。",
        ),
    ]
)
