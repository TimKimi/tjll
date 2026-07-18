"""文本与 JSON 字段清洗。"""

from __future__ import annotations

import json
import re
from typing import Any


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


def normalize_jsonish(value: Any) -> str | None:
    """清洗 categories / address / hours 等嵌套 JSON 字符串，去掉多余转义。

    - dict/list → compact JSON 字符串（ensure_ascii=False）
    - str → json.loads 后再 dumps；失败则 strip 原串
    - None → None
    """
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return ""
        try:
            parsed = json.loads(s)
        except (json.JSONDecodeError, TypeError):
            return s
        if isinstance(parsed, (dict, list)):
            return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
        return str(parsed)
    return str(value)
