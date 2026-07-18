"""document.clean 单元测试。"""

from __future__ import annotations

from backend.rag.document.clean import clean_text


def test_clean_text_empty():
    assert clean_text("") == ""


def test_clean_text_strips_null_bytes():
    assert clean_text("a\x00b") == "ab"


def test_clean_text_normalizes_newlines_and_spaces():
    raw = "hello  \tworld\r\n\r\n\r\nnext\rline  "
    out = clean_text(raw)
    assert "\r" not in out
    assert "\n\n\n" not in out
    assert "  " not in out
    assert out.startswith("hello")
    assert "next" in out
