#!/usr/bin/env python
"""查看数据库内容 —— 检查 Yelp 数据是否正确存储。

用法：
    uv run python backend/tests/scripts/check_db.py
    uv run python backend/tests/scripts/check_db.py --businesses 20
    uv run python backend/tests/scripts/check_db.py --reviews 10
"""

from __future__ import annotations

import argparse

from sqlalchemy import text

from backend.database import async_session, engine
from backend.models.base import Base


async def show_businesses(limit: int = 10):
    """打印商家列表。"""
    async with async_session() as session:
        rows = await session.execute(
            text(
                "SELECT id, name, rating, review_count, price, "
                "       LEFT(categories, 80) AS cats, "
                "       stored_at::date AS stored "
                "FROM businesses "
                "ORDER BY stored_at DESC "
                "LIMIT :lim"
            ),
            {"lim": limit},
        )
        results = rows.all()
        print(f"\n{'=' * 80}")
        print(f"  商家表 (businesses) — 共 {len(results)} 条")
        print(f"{'=' * 80}")
        print(
            f"{'ID':<24} {'名称':<28} {'评分':>4} {'评论':>6} {'价格':>4}  {'存储时间'}"
        )
        print(f"{'-' * 24} {'-' * 28} {'-' * 4} {'-' * 6} {'-' * 4}  {'-' * 10}")
        for r in results:
            print(
                f"{r.id:<24} {r.name:<28} {r.rating:>4.1f} {r.review_count:>6} "
                f"{r.price or '':>4}  {r.stored}"
            )


async def show_reviews(limit: int = 10):
    """打印评论列表。"""
    async with async_session() as session:
        rows = await session.execute(
            text(
                "SELECT r.id, r.business_id, r.rating, "
                "       LEFT(r.text, 100) AS text_preview, "
                "       b.name AS biz_name, "
                "       r.stored_at::date AS stored "
                "FROM reviews r "
                "LEFT JOIN businesses b ON b.id = r.business_id "
                "ORDER BY r.stored_at DESC "
                "LIMIT :lim"
            ),
            {"lim": limit},
        )
        results = rows.all()
        print(f"\n{'=' * 80}")
        print(f"  评论表 (reviews) — 共 {len(results)} 条")
        print(f"{'=' * 80}")
        for r in results:
            print(f"\n  [{r.rating}★] 商家: {r.biz_name} (ID: {r.business_id})")
            print(f"  评论 ID: {r.id}")
            print(f"  内容: {r.text_preview}...")
            print(f"  存储时间: {r.stored}")


async def show_stats():
    """显示数据统计。"""
    async with async_session() as session:
        biz_count = (
            await session.execute(text("SELECT COUNT(*) FROM businesses"))
        ).scalar()
        rev_count = (
            await session.execute(text("SELECT COUNT(*) FROM reviews"))
        ).scalar()
        avg_rating = (
            await session.execute(
                text(
                    "SELECT ROUND(AVG(rating)::numeric, 2) FROM businesses WHERE rating > 0"
                )
            )
        ).scalar()
        top_biz = (
            await session.execute(
                text(
                    "SELECT name, rating, review_count FROM businesses ORDER BY review_count DESC LIMIT 3"
                )
            )
        ).all()
        top_reviewed = (
            await session.execute(
                text(
                    "SELECT b.name, COUNT(r.id) AS rc FROM businesses b "
                    "JOIN reviews r ON r.business_id = b.id "
                    "GROUP BY b.name ORDER BY rc DESC LIMIT 3"
                )
            )
        ).all()

    print(f"\n{'=' * 80}")
    print("  数据库统计")
    print(f"{'=' * 80}")
    print(f"  商家总数:     {biz_count}")
    print(f"  评论总数:     {rev_count}")
    print(f"  平均评分:     {avg_rating or 'N/A'}")
    print("\n  评论最多的商家:")
    for b, c in top_reviewed:
        print(f"    - {b}: {c} 条评论")
    print("\n  最热门的商家:")
    for r in top_biz:
        print(f"    - {r.name}: {r.rating}★ ({r.review_count} 条评论)")


async def main():
    parser = argparse.ArgumentParser(description="查看数据库内容")
    parser.add_argument("--businesses", type=int, default=10, help="显示商家数")
    parser.add_argument("--reviews", type=int, default=10, help="显示评论数")
    args = parser.parse_args()

    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await show_stats()
    await show_businesses(args.businesses)
    await show_reviews(args.reviews)

    await engine.dispose()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
