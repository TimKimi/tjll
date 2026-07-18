"""离线将 cleaned Yelp JSON 切分嵌入并写入 OpenSearch。

用法：
  # 补写：只入库进度里没有的商家
  uv run python -m backend.rag.scripts.index_cleaned_yelp --mode backfill
  # 复写：全部商家重新入库（不删索引，同 chunk_id 覆盖）
  uv run python -m backend.rag.scripts.index_cleaned_yelp --mode rewrite
  # 删除并重建索引后再复写
  uv run python -m backend.rag.scripts.index_cleaned_yelp --mode rewrite --recreate

进度文件：data/yelp-dataset/cleaned/index_progress.json
仅当某商家好评与坏评均成功写入后才记录其 id。
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Literal

from backend.config import settings
from backend.rag.document.index_progress import (
    both_sides_fully_indexed,
    clear_indexed,
    index_progress_path,
    list_business_json_files,
    load_indexed_ids,
    mark_indexed,
)
from backend.rag.document.indexing import index_business_summaries_to_opensearch
from backend.rag.opensearch.schema import ensure_index

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

Mode = Literal["backfill", "rewrite"]


def _default_cleaned_dir() -> Path:
    return settings.yelp_dataset_dir / "cleaned"


def run_index(args: argparse.Namespace) -> int:
    cleaned_dir = Path(args.input_dir) if args.input_dir else _default_cleaned_dir()
    if not cleaned_dir.is_dir():
        raise FileNotFoundError(
            f"cleaned 目录不存在: {cleaned_dir}\n"
            "请先运行 just review-clean ... 生成 cleaned JSON。"
        )

    mode: Mode = args.mode
    progress_file = index_progress_path(cleaned_dir)
    files = list_business_json_files(cleaned_dir)

    if args.limit is not None:
        files = files[: max(0, args.limit)]

    if not files:
        logger.warning("未找到任何商家 JSON：%s/*.json", cleaned_dir)
        return 0

    index_name = args.index or settings.opensearch_index
    ensure_index(index_name, recreate=args.recreate)

    if mode == "rewrite":
        # 复写：清空进度，按完整入库结果重建；索引本身不删（除非 --recreate）
        clear_indexed(progress_file)
        already: set[str] = set()
    else:
        already = load_indexed_ids(progress_file)

    logger.info(
        "模式=%s 索引=%s recreate=%s 文件数=%d 已入库=%d dir=%s progress=%s",
        mode,
        index_name,
        args.recreate,
        len(files),
        len(already),
        cleaned_dir,
        progress_file.name,
    )

    total_chunks = 0
    total_success = 0
    total_errors = 0
    businesses_ok = 0
    businesses_skipped = 0
    businesses_incomplete = 0
    businesses_empty = 0

    for path in files:
        raw = json.loads(path.read_text(encoding="utf-8"))
        business_id = str(raw.get("id") or path.stem)

        if mode == "backfill" and business_id in already:
            businesses_skipped += 1
            logger.info("跳过已入库: %s", business_id)
            continue

        result = index_business_summaries_to_opensearch(
            raw,
            index_name=index_name,
            ensure=False,
        )
        chunks = int(result.get("chunks") or 0)
        success = int(result.get("success") or 0)
        errors = result.get("errors") or []
        total_chunks += chunks
        total_success += success
        total_errors += len(errors) if isinstance(errors, list) else int(errors or 0)

        if chunks == 0:
            businesses_empty += 1
            logger.info("跳过空 summary: %s", path.name)
            continue

        if both_sides_fully_indexed(result):
            mark_indexed(progress_file, business_id)
            already.add(business_id)
            businesses_ok += 1
            logger.info(
                "完整入库 %s pos=%d neg=%d chunks=%d",
                business_id,
                result.get("positive_chunks"),
                result.get("negative_chunks"),
                chunks,
            )
        else:
            businesses_incomplete += 1
            logger.warning(
                "未记进度（双侧未完整）%s pos=%s neg=%s errors=%s success=%s/%s",
                business_id,
                result.get("positive_chunks"),
                result.get("negative_chunks"),
                errors,
                success,
                chunks,
            )

    logger.info(
        "完成: mode=%s ok=%d skipped=%d incomplete=%d empty=%d "
        "chunks=%d success=%d error_items=%d",
        mode,
        businesses_ok,
        businesses_skipped,
        businesses_incomplete,
        businesses_empty,
        total_chunks,
        total_success,
        total_errors,
    )
    return 0 if total_errors == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Index cleaned Yelp JSON into OpenSearch (backfill / rewrite)"
    )
    parser.add_argument(
        "--mode",
        choices=("backfill", "rewrite"),
        default="backfill",
        help="backfill=只补未入库商家；rewrite=全部复写覆盖（默认 backfill）",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="cleaned JSON 目录（默认 data/yelp-dataset/cleaned）",
    )
    parser.add_argument(
        "--index",
        type=str,
        default=None,
        help=f"目标索引名（默认 {settings.opensearch_index}）",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="删除并重建索引后再入库（通常配合 rewrite）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="最多处理的 JSON 文件数（调试用）",
    )
    args = parser.parse_args(argv)
    try:
        return run_index(args)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
