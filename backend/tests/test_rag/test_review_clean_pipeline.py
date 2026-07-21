"""rag.review_clean.config / pipeline 纯逻辑单元测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.data.schemas import ConvertedBusiness, ConvertedReview
from backend.rag.review_clean.config import CleanLocalConfig
from backend.rag.review_clean.pipeline import (
    _append_delta,
    _star_needs,
    _trim_review,
    clean_business,
    parse_extract_deltas,
)


def _cfg(
    *,
    n_ctx: int = 4096,
    prompt_reserve_tokens: int = 600,
    extract_n_predict: int = 64,
    n_predict: int = 128,
    target_chars: int = 50,
) -> CleanLocalConfig:
    return CleanLocalConfig(
        model_dir=Path("."),
        model_path=Path("m.gguf"),
        llama_cli=Path("cli.exe"),
        llama_server=Path("server.exe"),
        server_host="127.0.0.1",
        server_port=18080,
        n_ctx=n_ctx,
        n_gpu_layers=99,
        n_predict=n_predict,
        extract_n_predict=extract_n_predict,
        prompt_reserve_tokens=prompt_reserve_tokens,
        target_chars=target_chars,
    )


def test_input_char_budget():
    cfg = _cfg(n_ctx=1000, prompt_reserve_tokens=100, extract_n_predict=100)
    assert cfg.input_char_budget == (1000 - 100 - 100) * 2


def test_parse_extract_deltas():
    from backend.llm.prompts.review_clean import NEGATIVE_MARKER, POSITIVE_MARKER

    text = f"{POSITIVE_MARKER}\n干净卫生\n{NEGATIVE_MARKER}\n排队久"
    pos, neg = parse_extract_deltas(text)
    assert "干净" in pos
    assert "排队" in neg

    pos2, neg2 = parse_extract_deltas(
        f"{POSITIVE_MARKER}\nEMPTY\n{NEGATIVE_MARKER}\nEMPTY"
    )
    assert pos2 == ""
    assert neg2 == ""


def test_star_needs():
    assert _star_needs(5) == (True, False)
    assert _star_needs(4) == (True, True)
    assert _star_needs(3) == (False, True)
    assert _star_needs(None) == (True, True)


def test_append_delta_and_trim():
    joined, full = _append_delta("", "很好吃", target=10)
    assert joined == "很好吃"
    assert full is False

    joined2, _ = _append_delta("前文", "后续", target=100)
    assert "。" in joined2

    trimmed = _trim_review("x" * 100, budget=50)
    assert trimmed.endswith("…")
    assert len(trimmed) == 64  # max(64, budget) - 1 + ellipsis


class _FakeClient:
    def __init__(self) -> None:
        self.calls = 0

    def chat(self, system: str, user: str, *, max_tokens: int | None = None) -> str:
        self.calls += 1
        from backend.llm.prompts.review_clean import NEGATIVE_MARKER, POSITIVE_MARKER

        if "润色" in system or "待润色" in user:
            return "润色后的正文"
        return f"{POSITIVE_MARKER}\n服务好态度佳\n{NEGATIVE_MARKER}\nEMPTY"


def test_clean_business_no_reviews():
    biz = ConvertedBusiness(id="b1", name="店A")
    out = clean_business(biz, [], cfg=_cfg(), client=_FakeClient(), shard=0)
    assert out["positive_summary"] == ""
    assert out["clean_meta"]["skipped_reason"] == "no_reviews_after_length_filter"


def test_clean_business_happy_path():
    biz = ConvertedBusiness(id="b1", name="店A", rating=5.0)
    reviews = [
        ConvertedReview(
            id="r1",
            business_id="b1",
            text="这是一条足够长的好评内容，环境干净卫生服务很好",
            rating=5,
            time_created="2024-01-02 10:00:00",
        ),
        ConvertedReview(
            id="r2",
            business_id="b1",
            text="短",
            rating=5,
            time_created="2024-01-01 10:00:00",
        ),
    ]
    client = _FakeClient()
    out = clean_business(
        biz,
        reviews,
        cfg=_cfg(target_chars=20),
        client=client,
        shard=1,
        max_reviews=10,
    )
    assert out["positive_summary"]
    assert out["clean_meta"]["shard"] == 1
    assert out["clean_meta"]["llm_calls"] >= 1
    assert client.calls >= 1


def test_load_clean_config_missing(tmp_path):
    from backend.rag.review_clean.config import load_clean_config

    with pytest.raises(FileNotFoundError, match="缺少旁路配置"):
        load_clean_config(tmp_path)
