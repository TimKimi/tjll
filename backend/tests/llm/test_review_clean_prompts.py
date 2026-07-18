"""llm.prompts.review_clean 轻量测试。"""

from __future__ import annotations

from backend.llm.prompts.review_clean import (
    EMPTY_DELTA,
    EXTRACT_SYSTEM,
    EXTRACT_USER_TEMPLATE,
    NEGATIVE_MARKER,
    POLISH_SYSTEM,
    POSITIVE_MARKER,
)


def test_review_clean_prompt_markers():
    assert POSITIVE_MARKER in EXTRACT_SYSTEM
    assert NEGATIVE_MARKER in EXTRACT_SYSTEM
    assert EMPTY_DELTA == "EMPTY"
    user = EXTRACT_USER_TEMPLATE.format(
        business_name="店",
        rating=5,
        need_pos="是",
        need_neg="否",
        review="很好",
    )
    assert "很好" in user
    assert "100" in POLISH_SYSTEM.format(target_chars=100)
