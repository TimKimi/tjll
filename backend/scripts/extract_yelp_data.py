#!/usr/bin/env python
"""Yelp 学术数据集 — 一次性解压 & 加载脚本。

使用方法：
    # 1. 确保 Docker PostgreSQL 正在运行
    docker compose up -d

    # 2. 运行提取和加载（全部数据）
    uv run python backend/scripts/extract_yelp_data.py

    # 3. 仅加载少量数据进行测试
    uv run python backend/scripts/extract_yelp_data.py --max-businesses 100 --max-reviews 500

    # 4. 查看帮助
    uv run python backend/scripts/extract_yelp_data.py --help

处理流程：
    1. 解压 data/Yelp-JSON.zip → 获取 yelp_dataset.tar
    2. 从 tar 中提取 JSONL 文件到 data/yelp-dataset/
    3. 流式读取 JSONL 并映射到 ORM 模型
    4. 批量写入 PostgreSQL
"""

from __future__ import annotations

import argparse
import logging
import os
import tarfile
import time
import zipfile
from pathlib import Path

# 确保 backend 包可导入
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


# ============================================================
# 第一步：解压
# ============================================================


def extract_zip_and_tar(zip_path: Path, extract_dir: Path) -> dict[str, Path]:
    """解压 zip → tar → JSONL 文件。

    Args:
        zip_path: 压缩包路径。
        extract_dir: 提取目标目录。

    Returns:
        JSONL 文件路径字典: {名称: 路径}
    """
    extract_dir.mkdir(parents=True, exist_ok=True)
    jsonl_files: dict[str, Path] = {}

    logger.info("步骤 1/2: 解压 %s", zip_path)

    with zipfile.ZipFile(str(zip_path), "r") as zf:
        # 检查 tar 是否在 zip 中
        if TAR_NAME not in zf.namelist():
            # 也许直接包含 JSONL 文件
            for name in zf.namelist():
                if name.endswith(".json") and not name.startswith("__MACOSX"):
                    logger.info("  发现 JSONL: %s", name)
                    target = extract_dir / Path(name).name
                    if not target.exists():
                        with zf.open(name) as src, open(target, "wb") as dst:
                            dst.write(src.read())
                        logger.info("  解压到: %s", target)
                    jsonl_files[Path(name).stem] = target
            return jsonl_files

        # 从 zip 中读取 tar
        tar_data = zf.read(TAR_NAME)
        logger.info("  tar 大小: %.1f MB", len(tar_data) / (1024 * 1024))

        # 从 tar 中提取 JSONL
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


# ============================================================
# 第二步：加载到数据库
# ============================================================


async def load_to_database(
    jsonl_files: dict[str, Path],
    max_businesses: int | None = None,
    max_reviews: int | None = None,
    batch_size: int = 500,
) -> dict:
    """将解压后的 JSONL 数据加载到 PostgreSQL。

    Args:
        jsonl_files: 文件路径字典。
        max_businesses: 限制最大商家数。
        max_reviews: 限制最大评论数。
        batch_size: 每批写入数量。

    Returns:
        加载统计信息。
    """
    from backend.database import engine
    from backend.models.base import Base

    # 确保表存在
    logger.info("步骤 2/2: 确保数据库表存在...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("  表已就绪")

    # 加载商家
    from backend.data.loader import load_businesses, load_reviews

    stats = {}

    biz_file = jsonl_files.get("yelp_academic_dataset_business")
    if biz_file:
        logger.info("加载商家数据: %s", biz_file)
        stats["businesses"] = await load_businesses(
            file_path=biz_file, batch_size=batch_size, max_rows=max_businesses
        )
    else:
        logger.warning("未找到商家数据文件")

    rev_file = jsonl_files.get("yelp_academic_dataset_review")
    if rev_file:
        logger.info("加载评论数据: %s", rev_file)
        stats["reviews"] = await load_reviews(
            file_path=rev_file, batch_size=batch_size, max_rows=max_reviews
        )
    else:
        logger.warning("未找到评论数据文件")

    await engine.dispose()
    return stats


# ============================================================
# 主入口
# ============================================================


async def main():
    parser = argparse.ArgumentParser(
        description="Yelp 学术数据集 — 解压并加载到 PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  uv run python backend/scripts/extract_yelp_data.py
  uv run python backend/scripts/extract_yelp_data.py --max-businesses 1000 --batch-size 200
  uv run python backend/scripts/extract_yelp_data.py --skip-extract
  uv run python backend/scripts/extract_yelp_data.py --skip-load
        """,
    )
    parser.add_argument(
        "--max-businesses",
        type=int,
        default=None,
        help="最大商家数（默认全部）",
    )
    parser.add_argument(
        "--max-reviews",
        type=int,
        default=None,
        help="最大评论数（默认全部）",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="每批写入数据库的行数（默认 500）",
    )
    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="跳过解压，假定 data/yelp-dataset/ 中已有 JSONL",
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="仅解压，不加载到数据库",
    )
    args = parser.parse_args()

    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Yelp 学术数据集 — 加载开始")
    logger.info("=" * 60)

    # 步骤 1: 解压
    jsonl_files = {}
    if not args.skip_extract:
        jsonl_files = extract_zip_and_tar(ZIP_PATH, EXTRACT_DIR)
    else:
        logger.info("跳过解压，扫描 %s", EXTRACT_DIR)
        for f in EXTRACT_DIR.iterdir():
            if f.suffix == ".json":
                jsonl_files[f.stem] = f
        logger.info("  发现 %d 个 JSONL 文件", len(jsonl_files))

    # 步骤 2: 加载
    if not args.skip_load:
        if not jsonl_files:
            logger.error("没有 JSONL 文件可加载！")
            return
        stats = await load_to_database(
            jsonl_files,
            max_businesses=args.max_businesses,
            max_reviews=args.max_reviews,
            batch_size=args.batch_size,
        )
        elapsed = time.time() - start_time

        logger.info("=" * 60)
        logger.info("加载完成！耗时 %.1f 秒", elapsed)
        logger.info("=" * 60)

        biz_stat = stats.get("businesses", {})
        rev_stat = stats.get("reviews", {})
        logger.info(
            "  商家: 总计 %(total)s, 插入 %(inserted)s, 跳过 %(skipped)s", biz_stat
        )
        logger.info(
            "  评论: 总计 %(total)s, 插入 %(inserted)s, 跳过 %(skipped)s", rev_stat
        )
    else:
        logger.info("跳过数据库加载（--skip-load）")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
