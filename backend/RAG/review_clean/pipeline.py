"""单商家清洗：短增量抽取追加 + 星级分流 + 最终润色。"""

from __future__ import annotations

import logging
import re
from typing import Any

from backend.LLM.prompts.review_clean import (
    EMPTY_DELTA,
    EXTRACT_SYSTEM,
    EXTRACT_USER_TEMPLATE,
    NEGATIVE_MARKER,
    POLISH_SYSTEM,
    POLISH_USER_TEMPLATE,
    POSITIVE_MARKER,
)
from backend.data.schemas import ConvertedBusiness, ConvertedReview
from backend.RAG.review_clean.batching import MIN_REVIEW_CHARS
from backend.RAG.review_clean.config import CleanLocalConfig
from backend.RAG.review_clean.llama_client import LlamaServerClient

logger = logging.getLogger(__name__)


def parse_extract_deltas(text: str) -> tuple[str, str]:
    """解析抽取输出为 (pos_delta, neg_delta)；无内容则为空串。"""
    cleaned = text.strip()
    pos_raw = ""
    neg_raw = ""
    if POSITIVE_MARKER in cleaned and NEGATIVE_MARKER in cleaned:
        after = cleaned.split(POSITIVE_MARKER, 1)[1]
        if NEGATIVE_MARKER in after:
            pos_raw, neg_raw = after.split(NEGATIVE_MARKER, 1)
        else:
            pos_raw = after
    elif POSITIVE_MARKER in cleaned:
        pos_raw = cleaned.split(POSITIVE_MARKER, 1)[1]
    elif NEGATIVE_MARKER in cleaned:
        neg_raw = cleaned.split(NEGATIVE_MARKER, 1)[1]
    else:
        # 容错：整段当好评增量
        pos_raw = cleaned

    def _norm(s: str) -> str:
        s = s.strip()
        s = re.sub(rf"{re.escape(POSITIVE_MARKER)}|{re.escape(NEGATIVE_MARKER)}", "", s)
        s = s.strip()
        if not s or s.upper() == EMPTY_DELTA or s in ("无", "无内容", "（空）", "(空)"):
            return ""
        return s

    return _norm(pos_raw), _norm(neg_raw)


def _star_needs(rating: int | float | None) -> tuple[bool, bool]:
    """按星级决定是否需要好评/坏评增量。

    - r > 4：只抽好评（如 4.5、5）
    - 3 < r <= 4：好评、坏评都抽（如 3.5、4；不含 3）
    - r <= 3：只抽坏评（如 1、2、3）
    """
    if rating is None:
        return True, True
    try:
        r = float(rating)
    except (TypeError, ValueError):
        return True, True
    if r > 4:
        return True, False
    if r > 3:  # (3, 4]
        return True, True
    return False, True


def _append_delta(container: str, delta: str, target: int) -> tuple[str, bool]:
    if not delta:
        return container, len(container) >= target
    piece = delta.strip()
    if not piece:
        return container, len(container) >= target
    if container and piece in container:
        return container, len(container) >= target
    if not container:
        joined = piece
    elif container[-1] in "。！？.!?;；":
        joined = container + piece
    else:
        joined = container + "。" + piece
    full = len(joined) >= target
    if len(joined) > target + 80:
        joined = joined[:target]
    return joined, full


def _trim_review(review: str, budget: int) -> str:
    if len(review) <= budget:
        return review
    return review[: max(64, budget) - 1] + "…"


def clean_business(
    business: ConvertedBusiness,
    reviews: list[ConvertedReview],
    *,
    cfg: CleanLocalConfig,
    client: LlamaServerClient,
    shard: int,
    max_reviews: int | None = 200,
    target_chars: int | None = None,
) -> dict[str, Any]:
    """从最新评论抽取短增量并追加；写满后停该侧；最后各润色一次。"""
    target = target_chars if target_chars is not None else cfg.target_chars
    extract_max = cfg.extract_n_predict
    polish_max = cfg.n_predict
    review_budget = max(256, cfg.input_char_budget)

    ordered = sorted(
        reviews,
        key=lambda r: r.time_created or "",
        reverse=True,
    )
    if max_reviews is not None and max_reviews > 0:
        ordered = ordered[:max_reviews]

    usable = [r for r in ordered if r.text and len(r.text.strip()) >= MIN_REVIEW_CHARS]
    if not usable:
        out = business.model_dump()
        out["positive_summary"] = ""
        out["negative_summary"] = ""
        out["clean_meta"] = {
            "shard": shard,
            "mode": "extract_append_polish",
            "skipped_reason": "no_reviews_after_length_filter",
            "reviews_raw": len(reviews),
            "reviews_scanned": 0,
            "llm_calls": 0,
            "target_chars": target,
            "pos_full": False,
            "neg_full": False,
        }
        return out

    pos = ""
    neg = ""
    pos_full = False
    neg_full = False
    llm_calls = 0
    scanned = 0

    logger.info(
        "商家 %s: raw=%d try=%d target_chars=%d extract_max_tokens=%d",
        business.id,
        len(reviews),
        len(usable),
        target,
        extract_max,
    )

    for i, rev in enumerate(usable, start=1):
        if pos_full and neg_full:
            break
        scanned = i
        need_pos, need_neg = _star_needs(rev.rating)
        need_pos = need_pos and not pos_full
        need_neg = need_neg and not neg_full
        if not need_pos and not need_neg:
            continue

        review_text = _trim_review(rev.text.strip(), review_budget)
        user = EXTRACT_USER_TEMPLATE.format(
            business_name=business.name,
            rating=rev.rating,
            need_pos="是" if need_pos else "否",
            need_neg="是" if need_neg else "否",
            review=review_text,
        )
        raw = client.chat(EXTRACT_SYSTEM, user, max_tokens=extract_max)
        llm_calls += 1
        d_pos, d_neg = parse_extract_deltas(raw)
        if not need_pos:
            d_pos = ""
        if not need_neg:
            d_neg = ""

        if d_pos and not pos_full:
            pos, pos_full = _append_delta(pos, d_pos, target)
            if pos_full:
                logger.info(
                    "  review %d/%d: 好评已写满 (%d>=%d)",
                    i,
                    len(usable),
                    len(pos),
                    target,
                )
        if d_neg and not neg_full:
            neg, neg_full = _append_delta(neg, d_neg, target)
            if neg_full:
                logger.info(
                    "  review %d/%d: 坏评已写满 (%d>=%d)",
                    i,
                    len(usable),
                    len(neg),
                    target,
                )

        if i == 1 or i % 10 == 0 or (pos_full and neg_full):
            logger.info(
                "  review %d/%d pos_len=%d neg_len=%d calls=%d "
                "pos_full=%s neg_full=%s star=%s",
                i,
                len(usable),
                len(pos),
                len(neg),
                llm_calls,
                pos_full,
                neg_full,
                rev.rating,
            )

    # 最终润色（每侧最多 1 次）
    if pos.strip():
        polish_sys = POLISH_SYSTEM.format(target_chars=target)
        user = POLISH_USER_TEMPLATE.format(
            business_name=business.name,
            polarity="好评",
            target_chars=target,
            draft=pos[: max(target + 200, review_budget)],
        )
        pos = client.chat(polish_sys, user, max_tokens=polish_max).strip() or pos
        llm_calls += 1
        logger.info("  好评润色完成 len=%d", len(pos))

    if neg.strip():
        polish_sys = POLISH_SYSTEM.format(target_chars=target)
        user = POLISH_USER_TEMPLATE.format(
            business_name=business.name,
            polarity="坏评",
            target_chars=target,
            draft=neg[: max(target + 200, review_budget)],
        )
        neg = client.chat(polish_sys, user, max_tokens=polish_max).strip() or neg
        llm_calls += 1
        logger.info("  坏评润色完成 len=%d", len(neg))

    out = business.model_dump()
    out["positive_summary"] = pos
    out["negative_summary"] = neg
    out["clean_meta"] = {
        "shard": shard,
        "mode": "extract_append_polish",
        "reviews_raw": len(reviews),
        "reviews_scanned": scanned,
        "reviews_capped_to": max_reviews,
        "llm_calls": llm_calls,
        "target_chars": target,
        "pos_len": len(pos),
        "neg_len": len(neg),
        "pos_full": pos_full,
        "neg_full": neg_full,
        "extract_n_predict": extract_max,
    }
    return out
