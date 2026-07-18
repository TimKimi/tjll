"""短评过滤与按字符预算装箱。"""

from __future__ import annotations

MIN_REVIEW_CHARS = 15


def filter_short_reviews(
    texts: list[str], min_chars: int = MIN_REVIEW_CHARS
) -> list[str]:
    return [t.strip() for t in texts if t and len(t.strip()) >= min_chars]


def pack_by_char_budget(
    items: list[str],
    char_budget: int,
    *,
    joiner: str = "\n\n",
) -> list[list[str]]:
    """将字符串列表装箱，使 join 后长度尽量不超过 char_budget。

    单条超长时截断尾部后单独成批。
    """
    if char_budget < 64:
        raise ValueError("char_budget 过小")
    if not items:
        return []

    batches: list[list[str]] = []
    current: list[str] = []
    current_len = 0

    for raw in items:
        item = raw
        if len(item) > char_budget:
            item = item[: char_budget - 1] + "…"

        add_len = len(item) + (len(joiner) if current else 0)
        if current and current_len + add_len > char_budget:
            batches.append(current)
            current = [item]
            current_len = len(item)
        else:
            current.append(item)
            current_len += add_len

    if current:
        batches.append(current)
    return batches
