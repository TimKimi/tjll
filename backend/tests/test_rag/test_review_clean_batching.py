"""rag.review_clean.batching 单元测试。"""

from __future__ import annotations

import pytest

from backend.rag.review_clean.batching import filter_short_reviews, pack_by_char_budget


def test_filter_short_reviews():
    texts = ["short", "long-enough-review-text", "   ", "abcdefghijklmnop"]
    out = filter_short_reviews(texts, min_chars=10)
    assert out == ["long-enough-review-text", "abcdefghijklmnop"]


def test_pack_by_char_budget_basic():
    batches = pack_by_char_budget(["aa", "bb", "cccc"], char_budget=100, joiner="|")
    assert batches
    assert all(isinstance(b, list) for b in batches)


def test_pack_by_char_budget_empty():
    assert pack_by_char_budget([], char_budget=100) == []


def test_pack_by_char_budget_too_small():
    with pytest.raises(ValueError, match="char_budget"):
        pack_by_char_budget(["a"], char_budget=10)


def test_pack_truncates_oversized_item():
    batches = pack_by_char_budget(["x" * 200], char_budget=64)
    assert len(batches) == 1
    assert len(batches[0]) == 1
    assert batches[0][0].endswith("…")
    assert len(batches[0][0]) == 64
