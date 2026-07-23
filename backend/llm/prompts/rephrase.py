"""查询重述 Prompt：融合历史、属性片段与文档片段。"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

REPHRASE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你的任务是根据历史对话、相关属性与相关文档，把用户最新问题改写成一条独立、完整的检索查询。\n"
            "规则：\n"
            "1. 只输出改写后的检索文本本身，不要解释、不要引号；\n"
            '2. 补全指代词（"这个"、"那"、"它"）指向的具体对象；\n'
            "3. 输出须同时包含：清晰的问题表述 + 与问题相关的属性要点 + 与问题相关的文档要点"
            "（对属性/文档做摘要清洗，去掉无关噪音；若某块为「（无）」则忽略该块）；\n"
            "4. 如果原问题已经完整、无歧义且无额外属性/文档，可接近原样输出；\n"
            "5. 保持中文，不要翻译成英文。",
        ),
        MessagesPlaceholder("history"),
        (
            "human",
            "最新问题：{query}\n\n"
            "{insight_block}\n\n"
            "{attachment_block}\n\n"
            "改写后的检索查询：",
        ),
    ]
)
