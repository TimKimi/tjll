"""查询重述 Prompt（与 shixun/rag.py 一致）。"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

REPHRASE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你的任务是根据历史对话，把用户最新的问题改写成一个独立、完整、明确的检索查询。\n"
            "规则：\n"
            "1. 只输出改写后的问题本身，不要解释、不要引号；\n"
            '2. 补全指代词（"这个"、"那"、"它"）指向的具体对象；\n'
            "3. 如果原问题已经完整、无歧义，直接原样输出即可；\n"
            "4. 保持中文，不要翻译成英文。",
        ),
        MessagesPlaceholder("history"),
        ("human", "最新问题：{query}\n\n改写后："),
    ]
)
