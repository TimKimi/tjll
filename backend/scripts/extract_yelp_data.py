#!/usr/bin/env python
"""Yelp 学术数据集 — 两阶段加载脚本。

两阶段流程：
  第一阶段：扫描 JSON 文件，按条件筛选商家/评论/用户，构建三个待入库列表（不写 DB）
  第二阶段：将三个列表批量写入 PostgreSQL

用法：
    # 两阶段加载（推荐）：指定商家数和最低评论数
    uv run python backend/scripts/extract_yelp_data.py --max-businesses 50 --min-reviews 20

    # 查看帮助
    uv run python backend/scripts/extract_yelp_data.py --help

处理流程：
    1. 解压 data/Yelp-JSON.zip → 获取 yelp_dataset.tar
    2. 从 tar 中提取 JSONL 文件到 data/yelp-dataset/
    3. 第一阶段：扫描 JSON，构建商家/评论/用户列表，按条件过滤
    4. 第二阶段：批量写入 PostgreSQL
"""

from __future__ import annotations

import argparse
import logging
import os
import tarfile
import time
import zipfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
os.chdir(str(_REPO_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

ZIP_PATH = Path("data/Yelp-JSON.zip")
TAR_NAME = "Yelp JSON/yelp_dataset.tar"
EXTRACT_DIR = Path("data/yelp-dataset")


def extract_zip_and_tar(zip_path: Path, extract_dir: Path) -> dict[str, Path]:
    """解压 zip → tar → JSONL 文件。"""
    extract_dir.mkdir(parents=True, exist_ok=True)
    jsonl_files: dict[str, Path] = {}

    logger.info("步骤 1/2: 解压 %s", zip_path)
    with zipfile.ZipFile(str(zip_path), "r") as zf:
        if TAR_NAME not in zf.namelist():
            for name in zf.namelist():
                if name.endswith(".json") and not name.startswith("__MACOSX"):
                    target = extract_dir / Path(name).name
                    if not target.exists():
                        with zf.open(name) as src, open(target, "wb") as dst:
                            dst.write(src.read())
                    jsonl_files[Path(name).stem] = target
            return jsonl_files

        tar_data = zf.read(TAR_NAME)
        logger.info("  tar 大小: %.1f MB", len(tar_data) / (1024 * 1024))

        with tarfile.open(fileobj=__import__("io").BytesIO(tar_data)) as tf:
            for member in tf.getmembers():
                if not member.isfile() or not member.name.endswith(".json"):
                    continue
                logger.info(
                    "  发现 JSONL: %s (%.1f MB)",
                    member.name,
                    member.size / (1024 * 1024),
                )
                target = extract_dir / Path(member.name).name
                if target.exists():
                    logger.info("  已存在，跳过: %s", target)
                else:
                    src_file = tf.extractfile(member)
                    if src_file is not None:
                        with src_file, open(target, "wb") as dst:
                            dst.write(src_file.read())
                    logger.info("  解压到: %s", target)
                jsonl_files[Path(member.name).stem] = target

    logger.info("解压完成，共 %d 个文件", len(jsonl_files))
    return jsonl_files


async def run_load(
    jsonl_files: dict[str, Path],
    max_businesses: int | None = None,
    min_reviews: int = 0,
    batch_size: int = 500,
) -> dict:
    """执行两阶段加载。"""
    from backend.database import engine
    from backend.models.base import Base

    logger.info("确保数据库表存在...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # 修正已有列的长度（SQLAlchemy create_all 不修改已存在列）
        from sqlalchemy import text

        await conn.execute(
            text("ALTER TABLE users ALTER COLUMN yelping_since TYPE VARCHAR(20)")
        )
    logger.info("  表已就绪")

    from backend.data.loader import load_all_yelp_data

    biz_file: Path | None = jsonl_files.get("yelp_academic_dataset_business")
    rev_file: Path | None = jsonl_files.get("yelp_academic_dataset_review")
    usr_file: Path | None = jsonl_files.get("yelp_academic_dataset_user")
    if not biz_file or not rev_file:
        raise FileNotFoundError("缺少商家或评论 JSONL 文件")
    stats = await load_all_yelp_data(
        business_file=biz_file,
        review_file=rev_file,
        user_file=usr_file,
        batch_size=batch_size,
        max_businesses=max_businesses,
        min_reviews=min_reviews,
    )

    await engine.dispose()
    return stats


async def main():
    parser = argparse.ArgumentParser(
        description="Yelp 学术数据集 — 两阶段加载到 PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 指定商家数和最低评论数
  uv run python backend/scripts/extract_yelp_data.py --max-businesses 50 --min-reviews 20

  # 仅解压，不加载
  uv run python backend/scripts/extract_yelp_data.py --skip-load
        """,
    )
    parser.add_argument(
        "--max-businesses",
        type=int,
        default=50,
        help="最大商家数（默认 50）",
    )
    parser.add_argument(
        "--min-reviews",
        type=int,
        default=10,
        help="商家最低有效评论数（不足则丢弃，默认 10）",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="每批写入行数（默认 500）",
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="仅解压不加载",
    )
    args = parser.parse_args()

    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Yelp 学术数据集 — 两阶段加载")
    logger.info(
        "  商家上限: %s, 最低评论数: %d",
        args.max_businesses or "全部",
        args.min_reviews,
    )
    logger.info("=" * 60)

    # 优先使用已解压的文件，不存在则解压
    jsonl_files = {}
    if EXTRACT_DIR.exists():
        for f in EXTRACT_DIR.iterdir():
            if f.suffix == ".json":
                jsonl_files[f.stem] = f

    if not jsonl_files:
        if ZIP_PATH.exists():
            jsonl_files = extract_zip_and_tar(ZIP_PATH, EXTRACT_DIR)
        else:
            logger.error(
                "JSONL 文件不存在 (%s)，压缩包也不存在 (%s)", EXTRACT_DIR, ZIP_PATH
            )
            return

    # 加载
    if not args.skip_load:
        if not jsonl_files:
            logger.error("没有 JSONL 文件可加载！")
            return
        stats = await run_load(
            jsonl_files,
            max_businesses=args.max_businesses,
            min_reviews=args.min_reviews,
            batch_size=args.batch_size,
        )
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info("全部完成！耗时 %.1f 秒", elapsed)
        logger.info("=" * 60)
        filtered = stats.get("filtered", {})
        logger.info(
            "  入库: %(businesses)s 商家, %(reviews)s 评论, %(users)s 用户", filtered
        )
    else:
        logger.info("跳过数据库加载（--skip-load）")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
