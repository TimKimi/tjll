"""Yelp 学术数据集加载器。

功能：
  1. 从解压后的 JSONL 文件流式读取
  2. 将学术数据集字段映射到 ORM 模型字段（兼容现有表结构）
  3. 批量写入 PostgreSQL（自动跳过已存在的记录）
  4. 支持断点续传（基于已存在的记录自动跳过）

用法：
    from backend.data.loader import load_yelp_data
    await load_yelp_data()
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from json import dumps
from pathlib import Path
from typing import Any, AsyncIterator, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import async_session
from backend.models.business import Business
from backend.models.review import Review
from backend.models.user import User
from backend.data.schemas import (
    ConvertedBusiness,
    ConvertedReview,
    ConvertedUser,
    DatasetBusiness,
    DatasetReview,
    DatasetUser,
)

logger = logging.getLogger(__name__)

# ── 常量 ──────────────────────────────────────────────────────
BATCH_SIZE = 500  # 每批写入的行数
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "yelp-dataset"
BUSINESS_FILE = DATA_DIR / "yelp_academic_dataset_business.json"
REVIEW_FILE = DATA_DIR / "yelp_academic_dataset_review.json"

T = TypeVar("T")

# ── 星期映射（Yelp API 格式：0=周日）─────────────────────
_DAY_MAP = {
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6,
    "Sunday": 0,
}


# ============================================================
# 辅助函数：字段转换
# ============================================================


def _make_alias(name: str) -> str:
    """从商家名称生成 alias（小写、连字符）。"""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\- ]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:255] or "unknown"


def _parse_categories(cat_str: str | None) -> str | None:
    """将逗号分隔的分类字符串转为 Yelp API 格式的 JSON 数组。

    输入: "Doctors, Traditional Chinese Medicine, Acupuncture"
    输出: '[{"alias":"doctors","title":"Doctors"}]'
    """
    if not cat_str or not cat_str.strip():
        return None
    parts = [c.strip() for c in cat_str.split(",") if c.strip()]
    result = []
    for p in parts:
        alias = p.lower().replace(" & ", "-").replace("/", "-").replace(" ", "-")
        alias = re.sub(r"[^a-z0-9\-]", "", alias)
        result.append({"alias": alias, "title": p})
    return dumps(result, ensure_ascii=False)


def _make_address(address: str, city: str, state: str, zip_code: str) -> str:
    """将地址字段组合成 YelpLocation 格式的 JSON。"""
    loc = {
        "address1": address,
        "address2": "",
        "address3": "",
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "country": "US",
        "display_address": [
            address,
            f"{city}, {state} {zip_code}",
        ],
    }
    return dumps(loc, ensure_ascii=False)


def _parse_hours(hours: dict | None) -> str | None:
    """将学术数据集的 hours 格式转为 Yelp API 格式的 JSON。

    输入: {"Monday": "8:0-18:30", "Tuesday": "8:0-18:30", ...}
    输出: {"open": [{"is_overnight": false, "start": "0800", "end": "1830", "day": 1}, ...], "hours_type": "REGULAR"}
    """
    if not hours:
        return None

    open_list = []
    for day_name, time_range in hours.items():
        day_num = _DAY_MAP.get(day_name)
        if day_num is None:
            continue
        if not time_range or time_range.strip() == "" or time_range == "0:0-0:0":
            continue
        parts = time_range.split("-")
        if len(parts) != 2:
            continue
        start_str, end_str = parts[0].strip(), parts[1].strip()
        start_hm = start_str.split(":")
        end_hm = end_str.split(":")
        try:
            start_fmt = f"{int(start_hm[0]):02d}{int(start_hm[1]):02d}"
            end_fmt = f"{int(end_hm[0]):02d}{int(end_hm[1]):02d}"
        except (ValueError, IndexError):
            continue
        open_list.append(
            {
                "is_overnight": False,
                "start": start_fmt,
                "end": end_fmt,
                "day": day_num,
            }
        )

    if not open_list:
        return None

    return dumps(
        {"open": open_list, "hours_type": "REGULAR", "is_open_now": False},
        ensure_ascii=False,
    )


def convert_business(raw: DatasetBusiness) -> ConvertedBusiness:
    """将原始数据集商家数据转为 ORM 兼容格式。"""
    return ConvertedBusiness(
        id=raw.business_id,
        alias=_make_alias(raw.name),
        name=raw.name,
        is_closed=raw.is_open == 0,
        review_count=raw.review_count,
        rating=raw.stars,
        categories=_parse_categories(raw.categories),
        latitude=raw.latitude,
        longitude=raw.longitude,
        address=_make_address(raw.address, raw.city, raw.state, raw.postal_code),
        hours=_parse_hours(raw.hours),
    )


def convert_review(raw: DatasetReview) -> ConvertedReview:
    """将原始数据集评论数据转为 ORM 兼容格式。"""
    return ConvertedReview(
        id=raw.review_id,
        business_id=raw.business_id,
        text=raw.text,
        rating=int(raw.stars),
        time_created=raw.date,
        user=dumps({"id": raw.user_id}) if raw.user_id else None,
    )


def convert_user(raw: DatasetUser) -> ConvertedUser:
    """将原始数据集用户数据转为 ORM 兼容格式。

    注意：elite、friends 在 JSON 中已是逗号分隔字符串，
    直接存储，不做额外 JSON 编码。
    """
    return ConvertedUser(
        id=raw.user_id,
        name=raw.name,
        review_count=raw.review_count,
        yelping_since=raw.yelping_since,
        useful=raw.useful,
        funny=raw.funny,
        cool=raw.cool,
        fans=raw.fans,
        average_stars=raw.average_stars,
        elite=raw.elite or None,
        friends=raw.friends or None,
    )


# ============================================================
# JSONL 流式读取
# ============================================================


async def iter_jsonl(file_path: Path, model_cls: type[T]) -> AsyncIterator[T]:
    """流式读取 JSONL 文件，每行解析为一个 Pydantic 模型。

    在默认线程池中执行文件 I/O，每次读取 1MB 块后按行切分解析。
    """
    loop = asyncio.get_running_loop()
    chunk_size = 1 << 20  # 1MB
    buffer = ""

    def _read_chunk(f, size: int) -> str:
        return f.read(size)

    with open(file_path, mode="r", encoding="utf-8") as f:
        while True:
            chunk = await loop.run_in_executor(None, _read_chunk, f, chunk_size)
            if not chunk:
                break
            buffer += chunk
            lines = buffer.split("\n")
            buffer = lines[-1]
            for line in lines[:-1]:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield model_cls(**json.loads(line))
                except Exception as exc:
                    logger.warning("跳过无法解析的行: %s", exc)

    if buffer.strip():
        try:
            yield model_cls(**json.loads(buffer.strip()))
        except Exception as exc:
            logger.warning("跳过无法解析的行: %s", exc)


# ============================================================
# 批量插入
# ============================================================


async def _insert_business_batch(
    session: AsyncSession, records: list[ConvertedBusiness]
) -> int:
    """批量插入商家（跳过已存在的）。"""
    inserted = 0
    for rec in records:
        existing = await session.get(Business, rec.id)
        if existing:
            continue
        biz = Business(
            id=rec.id,
            alias=rec.alias,
            name=rec.name,
            image_url=rec.image_url,
            is_closed=rec.is_closed,
            url=rec.url,
            review_count=rec.review_count,
            rating=rec.rating,
            price=rec.price,
            categories=rec.categories,
            latitude=rec.latitude,
            longitude=rec.longitude,
            address=rec.address,
            phone=rec.phone,
            display_phone=rec.display_phone,
            hours=rec.hours,
            transactions=rec.transactions,
            photos=rec.photos,
            yelp_menu_url=rec.yelp_menu_url,
        )
        session.add(biz)
        inserted += 1
    await session.commit()
    return inserted


async def _insert_review_batch(
    session: AsyncSession, records: list[ConvertedReview]
) -> int:
    """批量插入评论（跳过已存在的和无效外键的）。

    逐条检查 business_id 是否存在，避免 ForeignKeyViolation 导致整个 batch 回滚。
    """
    inserted = 0
    for rec in records:
        existing = await session.get(Review, rec.id)
        if existing:
            continue
        # 检查商家是否存在（避免外键冲突）
        biz = await session.get(Business, rec.business_id)
        if biz is None:
            continue
        review = Review(
            id=rec.id,
            business_id=rec.business_id,
            url=rec.url,
            text=rec.text,
            rating=rec.rating,
            time_created=rec.time_created,
            user=rec.user,
        )
        session.add(review)
        inserted += 1
    await session.commit()
    return inserted


async def _insert_user_batch(
    session: AsyncSession, records: list[ConvertedUser]
) -> int:
    """批量插入用户（跳过已存在的）。"""
    inserted = 0
    for rec in records:
        existing = await session.get(User, rec.id)
        if existing:
            continue
        user = User(
            id=rec.id,
            name=rec.name,
            review_count=rec.review_count,
            yelping_since=rec.yelping_since,
            useful=rec.useful,
            funny=rec.funny,
            cool=rec.cool,
            fans=rec.fans,
            average_stars=rec.average_stars,
            elite=rec.elite,
            friends=rec.friends,
        )
        session.add(user)
        inserted += 1
    await session.commit()
    return inserted


# ============================================================
# 主加载函数
# ============================================================


async def load_businesses(
    file_path: Path = BUSINESS_FILE,
    batch_size: int = BATCH_SIZE,
    max_rows: int | None = None,
) -> dict:
    """加载商家数据。

    Args:
        file_path: JSONL 文件路径。
        batch_size: 每批写入数量。
        max_rows: 最大处理行数（用于测试）。

    Returns:
        统计信息。
    """
    if not file_path.exists():
        return {"status": "skipped", "reason": f"文件不存在: {file_path}"}

    stats: dict[str, Any] = {"total": 0, "inserted": 0, "skipped": 0, "errors": 0}
    batch: list[ConvertedBusiness] = []
    start_time = time.time()

    async with async_session() as session:
        async for raw in iter_jsonl(file_path, DatasetBusiness):
            try:
                converted = convert_business(raw)
                batch.append(converted)
                stats["total"] += 1

                if len(batch) >= batch_size:
                    inserted = await _insert_business_batch(session, batch)
                    stats["inserted"] += inserted
                    stats["skipped"] += len(batch) - inserted
                    batch.clear()

                    elapsed = time.time() - start_time
                    logger.info(
                        "商家: 已处理 %d 条, 插入 %d 条, 耗时 %.1f秒",
                        stats["total"],
                        stats["inserted"],
                        elapsed,
                    )

                if max_rows and stats["total"] >= max_rows:
                    break
            except Exception as exc:
                stats["errors"] += 1
                logger.warning("商家处理出错: %s", exc)

        if batch:
            inserted = await _insert_business_batch(session, batch)
            stats["inserted"] += inserted
            stats["skipped"] += len(batch) - inserted

    elapsed = time.time() - start_time
    stats["elapsed_seconds"] = round(elapsed, 1)
    logger.info(
        "商家加载完成: 总计 %d, 插入 %d, 跳过 %d, 错误 %d, 耗时 %.1f秒",
        stats["total"],
        stats["inserted"],
        stats["skipped"],
        stats["errors"],
        elapsed,
    )
    return stats


async def load_reviews(
    file_path: Path = REVIEW_FILE,
    batch_size: int = BATCH_SIZE,
    max_rows: int | None = None,
) -> dict:
    """加载评论数据。

    Args:
        file_path: JSONL 文件路径。
        batch_size: 每批写入数量。
        max_rows: 最大处理行数（用于测试）。

    Returns:
        统计信息。
    """
    if not file_path.exists():
        return {"status": "skipped", "reason": f"文件不存在: {file_path}"}

    stats: dict[str, Any] = {"total": 0, "inserted": 0, "skipped": 0, "errors": 0}
    batch: list[ConvertedReview] = []
    start_time = time.time()

    async with async_session() as session:
        async for raw in iter_jsonl(file_path, DatasetReview):
            try:
                converted = convert_review(raw)
                batch.append(converted)
                stats["total"] += 1

                if len(batch) >= batch_size:
                    try:
                        inserted = await _insert_review_batch(session, batch)
                        stats["inserted"] += inserted
                        stats["skipped"] += len(batch) - inserted
                    except Exception as exc:
                        await session.rollback()
                        stats["errors"] += len(batch)
                        logger.warning("评论批处理出错 (已回滚): %s", exc)
                    batch.clear()

                    elapsed = time.time() - start_time
                    logger.info(
                        "评论: 已处理 %d 条, 插入 %d 条, 耗时 %.1f秒",
                        stats["total"],
                        stats["inserted"],
                        elapsed,
                    )

                if max_rows and stats["total"] >= max_rows:
                    break
            except Exception as exc:
                stats["errors"] += 1
                logger.warning("评论处理出错: %s", exc)

        if batch:
            try:
                inserted = await _insert_review_batch(session, batch)
                stats["inserted"] += inserted
                stats["skipped"] += len(batch) - inserted
            except Exception as exc:
                await session.rollback()
                stats["errors"] += len(batch)
                logger.warning("评论批处理出错 (已回滚): %s", exc)

    elapsed = time.time() - start_time
    stats["elapsed_seconds"] = round(elapsed, 1)
    logger.info(
        "评论加载完成: 总计 %d, 插入 %d, 跳过 %d, 错误 %d, 耗时 %.1f秒",
        stats["total"],
        stats["inserted"],
        stats["skipped"],
        stats["errors"],
        elapsed,
    )
    return stats


# ============================================================
# 两阶段加载：先扫描 JSON 构建列表，再批量写入数据库
# ============================================================


async def scan_phase(
    business_file: Path | None = BUSINESS_FILE,
    review_file: Path | None = REVIEW_FILE,
    user_file: Path | None = None,
    max_businesses: int = 100,
    min_reviews: int = 10,
) -> dict[str, Any]:
    """第一阶段：扫描 JSON 文件，构建待入库的三个列表（不写数据库）。

    Args:
        business_file: 商家 JSONL 路径。
        review_file: 评论 JSONL 路径。
        user_file: 用户 JSONL 路径（为 None 时不加载用户）。
        max_businesses: 最大商家数。
        min_reviews: 商家最低有效评论数（不足则丢弃该商家）。

    Returns:
        {"businesses": [...], "reviews": [...], "users": [...]}
        均为 Converted* 对象的列表。
    """
    if not business_file or not review_file:
        raise FileNotFoundError("需要商家和评论 JSONL 文件路径")
    if user_file is None:
        user_file = DATA_DIR / "yelp_academic_dataset_user.json"

    t0 = time.time()
    logger.info("=" * 60)
    logger.info("第一阶段：扫描 JSON 文件")
    logger.info("=" * 60)

    # ── 步骤1: 扫描商家 ────────────────────────────────
    logger.info("扫描商家 (最低评论数=%d)...", min_reviews)
    all_biz: list[DatasetBusiness] = []
    async for raw in iter_jsonl(business_file, DatasetBusiness):
        if raw.review_count >= min_reviews:
            all_biz.append(raw)
    logger.info("  满足最低评论数的商家: %d", len(all_biz))

    # 按评论数降序排列，取评论数最高的商家
    all_biz.sort(key=lambda b: b.review_count, reverse=True)
    pool_size = max(max_businesses * 3, max_businesses + 500)
    candidates = all_biz[:pool_size]
    candidate_ids = {b.business_id for b in candidates}
    top_reviews = candidates[0].review_count if candidates else 0
    bottom_reviews = candidates[-1].review_count if candidates else 0
    logger.info(
        "  候选商家: %d (池大小=%d, 评论数范围 %d~%d)",
        len(candidates),
        pool_size,
        bottom_reviews,
        top_reviews,
    )

    # ── 步骤2: 扫描评论 ────────────────────────────────
    logger.info("扫描评论...")
    biz_reviews: dict[str, list[DatasetReview]] = {bid: [] for bid in candidate_ids}
    needed_users: set[str] = set()
    rev_total = 0
    async for raw in iter_jsonl(review_file, DatasetReview):
        if raw.business_id in candidate_ids:
            biz_reviews[raw.business_id].append(raw)
            needed_users.add(raw.user_id)
            rev_total += 1
    logger.info("  匹配评论: %d, 涉及用户: %d", rev_total, len(needed_users))

    # ── 步骤3: 扫描用户 ────────────────────────────────
    logger.info("扫描用户...")
    found_users: set[str] = set()
    user_pool: list[DatasetUser] = []
    if user_file and user_file.exists():
        async for raw in iter_jsonl(user_file, DatasetUser):
            if raw.user_id in needed_users:
                user_pool.append(raw)
                found_users.add(raw.user_id)
    logger.info("  找到用户: %d / %d", len(found_users), len(needed_users))

    # ── 步骤4: 过滤——去掉用户不存在的评论 ─────────────
    valid_reviews: list[DatasetReview] = []
    for bid, revs in biz_reviews.items():
        for rev in revs:
            if rev.user_id in found_users:
                valid_reviews.append(rev)
    logger.info("  用户存在的评论: %d / %d", len(valid_reviews), rev_total)

    # ── 步骤5: 过滤——按最低有效评论数筛选商家 ─────────
    rev_count: dict[str, int] = {}
    for rev in valid_reviews:
        rev_count[rev.business_id] = rev_count.get(rev.business_id, 0) + 1

    final_biz: list[DatasetBusiness] = []
    final_biz_ids: set[str] = set()
    dropped = 0
    for biz in candidates:
        cnt = rev_count.get(biz.business_id, 0)
        if cnt >= min_reviews:
            final_biz.append(biz)
            final_biz_ids.add(biz.business_id)
            if len(final_biz) >= max_businesses:
                break
        else:
            dropped += 1
    logger.info(
        "有效商家: %d (丢弃 %d，需满足 %d+ 条有效评论)",
        len(final_biz),
        dropped,
        min_reviews,
    )

    # ── 步骤6: 裁切评论和用户，只保留最终商家相关的 ────
    final_reviews = [r for r in valid_reviews if r.business_id in final_biz_ids]
    final_user_ids = {r.user_id for r in final_reviews}
    final_users = [u for u in user_pool if u.user_id in final_user_ids]

    logger.info(
        "最终统计: 商家=%d, 评论=%d, 用户=%d",
        len(final_biz),
        len(final_reviews),
        len(final_users),
    )
    logger.info("第一阶段扫描完成, 耗时 %.1f秒", time.time() - t0)

    # 转换成 ORM 兼容格式
    return {
        "businesses": [convert_business(b) for b in final_biz],
        "reviews": [convert_review(r) for r in final_reviews],
        "users": [convert_user(u) for u in final_users],
        "raw": {
            "biz_total": len(all_biz),
            "rev_total": rev_total,
            "user_found": len(found_users),
            "user_needed": len(needed_users),
        },
    }


async def load_phase(
    biz_list: list[ConvertedBusiness],
    review_list: list[ConvertedReview],
    user_list: list[ConvertedUser],
    batch_size: int = BATCH_SIZE,
) -> dict[str, Any]:
    """第二阶段：将扫描结果批量写入数据库。"""
    t0 = time.time()
    logger.info("=" * 60)
    logger.info("第二阶段：写入数据库")
    logger.info("=" * 60)

    stats: dict[str, Any] = {
        "businesses": {"total": len(biz_list), "inserted": 0},
        "users": {"total": len(user_list), "inserted": 0},
        "reviews": {"total": len(review_list), "inserted": 0},
    }

    async with async_session() as session:
        # 写入商家
        if biz_list:
            logger.info("写入 %d 个商家...", len(biz_list))
            for i in range(0, len(biz_list), batch_size):
                batch = biz_list[i : i + batch_size]
                inserted = await _insert_business_batch(session, batch)
                stats["businesses"]["inserted"] += inserted
                if (i // batch_size) % 5 == 0:
                    logger.info(
                        "  商家: %d/%d",
                        min(i + batch_size, len(biz_list)),
                        len(biz_list),
                    )

        # 写入用户
        if user_list:
            logger.info("写入 %d 个用户...", len(user_list))
            for i in range(0, len(user_list), batch_size):
                batch = user_list[i : i + batch_size]
                inserted = await _insert_user_batch(session, batch)
                stats["users"]["inserted"] += inserted

        # 写入评论
        if review_list:
            logger.info("写入 %d 条评论...", len(review_list))
            for i in range(0, len(review_list), batch_size):
                batch = review_list[i : i + batch_size]
                try:
                    inserted = await _insert_review_batch(session, batch)
                    stats["reviews"]["inserted"] += inserted
                except Exception as exc:
                    await session.rollback()
                    logger.warning("评论批处理出错 (已回滚): %s", exc)

    elapsed = time.time() - t0
    logger.info("第二阶段完成, 耗时 %.1f秒", elapsed)
    stats["elapsed_seconds"] = round(elapsed, 1)
    return stats


async def load_all_yelp_data(
    business_file: Path | None = BUSINESS_FILE,
    review_file: Path | None = REVIEW_FILE,
    user_file: Path | None = None,
    batch_size: int = BATCH_SIZE,
    max_businesses: int | None = None,
    min_reviews: int = 0,
) -> dict:
    """两阶段加载 Yelp 数据。

    Args:
        business_file: 商家 JSONL 路径。
        review_file: 评论 JSONL 路径。
        user_file: 用户 JSONL 路径。
        batch_size: 每批写入行数。
        max_businesses: 最大商家数（None=全部）。
        min_reviews: 商家最低有效评论数。

    Returns:
        合并的统计信息。
    """
    if not business_file or not review_file:
        raise FileNotFoundError("需要商家和评论 JSONL 文件路径")
    if max_businesses is None:
        raise ValueError("请指定 --max-businesses")

    scan_result = await scan_phase(
        business_file=business_file,
        review_file=review_file,
        user_file=user_file,
        max_businesses=max_businesses,
        min_reviews=min_reviews,
    )

    # 第二阶段：写入
    load_stats = await load_phase(
        biz_list=scan_result["businesses"],
        review_list=scan_result["reviews"],
        user_list=scan_result["users"],
        batch_size=batch_size,
    )

    load_stats["scan"] = scan_result["raw"]
    load_stats["filtered"] = {
        "businesses": len(scan_result["businesses"]),
        "reviews": len(scan_result["reviews"]),
        "users": len(scan_result["users"]),
    }
    return load_stats
