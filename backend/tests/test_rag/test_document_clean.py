"""document.clean 单元测试。"""

from __future__ import annotations

from backend.rag.document.clean import clean_text, normalize_jsonish


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


def test_normalize_jsonish_dict_and_list():
    assert normalize_jsonish({"a": 1}) == '{"a":1}'
    assert normalize_jsonish([{"alias": "cafes"}]) == '[{"alias":"cafes"}]'


def test_normalize_jsonish_escaped_string():
    escaped = '[{"alias": "pizza", "title": "Pizza"}]'
    assert normalize_jsonish(escaped) == '[{"alias":"pizza","title":"Pizza"}]'


def test_normalize_jsonish_invalid_keeps_strip():
    assert normalize_jsonish("  not-json  ") == "not-json"


def test_normalize_jsonish_none():
    assert normalize_jsonish(None) is None
