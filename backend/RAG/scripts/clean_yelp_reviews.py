"""离线 Yelp 评论清洗 CLI。

用法：
  uv run python -m backend.RAG.scripts.clean_yelp_reviews \\
    --max-businesses 50 --min-reviews 10 --shard 0 --start 0 --end 25

不写数据库；结果写入 data/yelp-dataset/cleaned/。
配置仅读旁路 config.local.toml，不改根 .env。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

from backend.config import settings
from backend.data.loader import scan_phase
from backend.data.schemas import ConvertedBusiness, ConvertedReview
from backend.RAG.review_clean.config import load_clean_config
from backend.RAG.review_clean.llama_client import LlamaServerClient
from backend.RAG.review_clean.pipeline import clean_business
from backend.RAG.review_clean.shard import (
    filter_shard_ids,
    load_progress,
    mark_completed,
    progress_path,
    slice_ids,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
# 关闭 httpx 刷屏（HTTP Request: ... 200 OK）
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def _build_review_index(
    reviews: list[ConvertedReview],
) -> dict[str, list[ConvertedReview]]:
    idx: dict[str, list[ConvertedReview]] = defaultdict(list)
    for r in reviews:
        idx[r.business_id].append(r)
    return idx


def _write_business_json(out_dir: Path, payload: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    bid = str(payload["id"])
    path = out_dir / f"{bid}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


async def run_clean(args: argparse.Namespace) -> int:
    dataset_dir: Path = settings.yelp_dataset_dir
    cleaned_dir = dataset_dir / "cleaned"
    prog_path = progress_path(dataset_dir, args.shard)

    required = [
        dataset_dir / "yelp_academic_dataset_business.json",
        dataset_dir / "yelp_academic_dataset_review.json",
        dataset_dir / "yelp_academic_dataset_user.json",
    ]
    missing = [p for p in required if not p.is_file()]
    if missing:
        alt_zip = Path(__file__).resolve().parents[2] / "data" / "Yelp-JSON.zip"
        hint_zip = (
            settings.yelp_zip_path
            if settings.yelp_zip_path.is_file()
            else (alt_zip if alt_zip.is_file() else settings.yelp_zip_path)
        )
        raise FileNotFoundError(
            "缺少已解压的 Yelp JSONL，scan_phase 无法运行。缺失：\n  - "
            + "\n  - ".join(str(p) for p in missing)
            + "\n\n请先解压数据集到 data/yelp-dataset/：\n"
            f"  1) 确保 zip 在 {settings.yelp_zip_path}"
            f"（当前可见备选: {hint_zip}）\n"
            "  2) uv run python -m backend.scripts.extract_yelp_data --skip-load\n"
            "解压完成后再执行 just review-clean ..."
        )

    cfg = load_clean_config()
    logger.info(
        "加载旁路配置: model=%s n_ctx=%d n_predict=%d target_chars=%d",
        cfg.model_path.name,
        cfg.n_ctx,
        cfg.n_predict,
        cfg.target_chars,
    )

    logger.info(
        "scan_phase: max_businesses=%d min_reviews=%d",
        args.max_businesses,
        args.min_reviews,
    )
    scan = await scan_phase(
        max_businesses=args.max_businesses,
        min_reviews=args.min_reviews,
    )
    businesses: list[ConvertedBusiness] = scan["businesses"]
    reviews: list[ConvertedReview] = scan["reviews"]
    biz_by_id = {b.id: b for b in businesses}
    reviews_by_biz = _build_review_index(reviews)

    all_ids = [b.id for b in businesses]
    shard_ids = filter_shard_ids(all_ids, args.shard)
    shard_total = len(shard_ids)
    end = args.end if args.end is not None else shard_total
    selected = slice_ids(shard_ids, args.start, end)

    already = load_progress(prog_path)
    todo = [bid for bid in selected if bid not in already]

    range_report = {
        "shard": args.shard,
        "shard_total": shard_total,
        "processed_range": [args.start, end],
        "range_notation": f"[{args.start}, {end})",
        "selected_count": len(selected),
        "skipped_already_done": len(selected) - len(todo),
        "todo_count": len(todo),
        "business_ids": selected,
        "todo_business_ids": todo,
    }
    logger.info(
        "分片范围: shard=%s shard_total=%s processed_range=[%s, %s) "
        "selected=%s todo=%s (skip_done=%s)",
        args.shard,
        shard_total,
        args.start,
        end,
        len(selected),
        len(todo),
        len(selected) - len(todo),
    )
    print(json.dumps(range_report, ensure_ascii=False, indent=2))

    if not todo:
        logger.info("本区间无待处理商家，结束。")
        return 0

    with LlamaServerClient(cfg) as client:
        for i, bid in enumerate(todo, start=1):
            biz = biz_by_id[bid]
            revs = reviews_by_biz.get(bid, [])
            logger.info(
                "[%d/%d] 清洗商家 %s (%s) reviews=%d",
                i,
                len(todo),
                bid,
                biz.name,
                len(revs),
            )
            payload = clean_business(
                biz,
                revs,
                cfg=cfg,
                client=client,
                shard=args.shard,
                max_reviews=args.max_reviews_per_business,
                target_chars=args.target_chars,
            )
            out_path = _write_business_json(cleaned_dir, payload)
            mark_completed(
                prog_path,
                bid,
                extra={
                    "last_run_range": [args.start, end],
                    "last_shard": args.shard,
                },
            )
            logger.info("已写入 %s", out_path)

    done_report = {
        **range_report,
        "completed_this_run": todo,
        "output_dir": str(cleaned_dir),
        "progress_file": str(prog_path),
    }
    print("--- run finished ---")
    print(json.dumps(done_report, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="离线 Yelp 评论增量清洗（本地 GGUF）")
    p.add_argument("--max-businesses", type=int, required=True)
    p.add_argument("--min-reviews", type=int, required=True)
    p.add_argument("--shard", type=int, choices=(0, 1), required=True)
    p.add_argument("--start", type=int, default=0, help="分片内起始下标（含）")
    p.add_argument(
        "--end",
        type=int,
        default=None,
        help="分片内结束下标（不含）；默认到分片末尾",
    )
    p.add_argument(
        "--max-reviews-per-business",
        type=int,
        default=200,
        help="每商家最多扫描的评论条数（写满可提前停；0=不截断）",
    )
    p.add_argument(
        "--target-chars",
        type=int,
        default=None,
        help="好评/坏评写满字数；默认读 config.local.toml 的 target_chars（800）",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.start < 0:
        logger.error("--start 必须 >= 0")
        return 2
    if args.end is not None and args.end < args.start:
        logger.error("--end 必须 >= --start")
        return 2
    try:
        return asyncio.run(run_clean(args))
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        logger.warning("用户中断")
        return 130


if __name__ == "__main__":
    sys.exit(main())
