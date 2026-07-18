"""文本清洗。"""

from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """清洗加载结果：去空字节、统一换行、压缩空白。"""
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 去掉行尾空白
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    # 压缩过多空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 压缩连续空格 / tab
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()
