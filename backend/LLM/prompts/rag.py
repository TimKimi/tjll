"""RAG 生成 Prompt（与 shixun/rag.py 一致）。"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个基于给定资料回答问题的助手。\n"
            "严格根据提供的资料回答用户问题。资料里没有相关信息时，"
            '明确回答"根据现有资料无法回答"，不要编造。\n'
            "回答要简洁、准确，必要时引用资料中的原文。",
        ),
        (
            "human",
            "【参考资料】\n{context}\n\n【问题】\n{query}\n\n【回答】",
        ),
    ]
)

RAG_PROMPT_WITH_HISTORY = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个基于给定资料回答问题的助手。\n"
            "严格根据提供的资料回答用户问题。资料里没有相关信息时，"
            '明确回答"根据现有资料无法回答"，不要编造。\n'
            "结合历史对话理解用户意图，回答简洁、准确。",
        ),
        MessagesPlaceholder("history"),
        (
            "human",
            "【参考资料】\n{context}\n\n【问题】\n{query}\n\n【回答】",
        ),
    ]
)
