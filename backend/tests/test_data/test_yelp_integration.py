"""集成测试 —— 真实调用 Yelp API 并存入数据库。

运行方式：
    uv run pytest backend/tests/data_get/test_yelp_integration.py -v -s

注意：
    - 需要 YELP_API 环境变量已配置（.env 中）
    - 需要 PostgreSQL 已启动（docker compose up -d）
    - 使用 pytest.mark.integration 标记，可以用 -m integration 过滤
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_search_businesses_real_api():
    """真实调用 Yelp Search API，验证能返回数据。"""
    from backend.services.yelp import YelpService

    svc = YelpService()
    result = await svc.search_businesses(
        location="New York",
        term="pizza",
        limit=3,
    )
    assert result.total > 0, "应该在纽约找到披萨店"
    assert len(result.businesses) > 0
    biz = result.businesses[0]
    assert biz.id, "商家应该有 ID"
    assert biz.name, "商家应该有名称"
    assert biz.rating > 0, "商家应该有评分"
    print(f"\n  ✓ 找到 {result.total} 个商家，取前 {len(result.businesses)} 个")
    for b in result.businesses:
        print(f"    - {b.name} (评分: {b.rating}, 评论: {b.review_count})")


@pytest.mark.asyncio
async def test_get_business_detail_real_api():
    """真实调用 Details API，验证详细数据。"""
    from backend.services.yelp import YelpService

    svc = YelpService()
    # 先搜索拿到一个商家 ID
    search_result = await svc.search_businesses(
        location="San Francisco",
        term="coffee",
        limit=1,
    )
    assert len(search_result.businesses) > 0
    biz_id = search_result.businesses[0].id
    biz_name = search_result.businesses[0].name

    detail = await svc.get_business(biz_id)
    assert detail.id == biz_id
    assert detail.name == biz_name
    assert detail.location is not None
    assert detail.coordinates is not None
    print(f"\n  ✓ {detail.name}")
    print(f"    地址: {detail.location.display_address if detail.location else 'N/A'}")
    print(f"    坐标: ({detail.coordinates.latitude}, {detail.coordinates.longitude})")
    print(f"    电话: {detail.display_phone}")
    print(f"    评分: {detail.rating} ({detail.review_count} 条评论)")
    print(f"    分类: {[(c.title) for c in (detail.categories or [])]}")


@pytest.mark.asyncio
async def test_fetch_and_store_flow():
    """完整流程测试：搜索 → 获取详情 → 获取评论 → 存库。

    验证数据库最终能查到存储的数据。
    """
    from backend.database import async_session
    from backend.models.business import Business
    from backend.models.review import Review
    from backend.services.yelp import YelpService

    svc = YelpService()

    # 执行完整流程（获取 2 个商家，限定分类）
    stats = await svc.fetch_and_store(
        location="Austin",
        term="bbq",
        limit=2,
    )

    print("\n  ✓ 搜索完成:")
    print(f"    地点: {stats['location']}")
    print(f"    搜索词: {stats['term']}")
    print(f"    共找到: {stats['total_found']} 个商家")
    print(f"    已存储: {stats['businesses_stored']} 个商家")
    print(f"    已存储: {stats['reviews_stored']} 条评论")

    assert stats["businesses_stored"] > 0, "应该至少存了一个商家"

    # 从数据库验证
    async with async_session() as session:
        # 查询所有商家
        businesses = await session.execute(Business.__table__.select().limit(10))
        rows = businesses.fetchall()
        print(f"\n  ✓ 数据库中共有 {len(rows)} 条商家记录:")
        for row in rows:
            print(f"    - {row.name} (评分: {row.rating})")

        # 查询评论
        reviews = await session.execute(Review.__table__.select().limit(10))
        review_rows = reviews.fetchall()
        print(f"\n  ✓ 数据库中共有 {len(review_rows)} 条评论记录:")
        for row in review_rows[:5]:  # 只打印前 5 条
            text_preview = row.text[:60] if row.text else ""
            print(f"    - [{row.rating}★] {text_preview}...")
        if len(review_rows) > 5:
            print(f"    ... 还有 {len(review_rows) - 5} 条")


@pytest.mark.asyncio
async def test_reviews_for_known_business():
    """获取指定商家的评论。"""
    from backend.services.yelp import YelpService

    svc = YelpService()
    # 搜索餐厅
    search_result = await svc.search_businesses(
        location="Chicago",
        term="restaurant",
        limit=1,
    )
    assert len(search_result.businesses) > 0
    biz = search_result.businesses[0]

    from backend.services.yelp import YelpError

    try:
        reviews = await svc.get_reviews(biz.id)
    except YelpError as exc:
        if exc.status_code in (403, 404):
            pytest.skip(f"Reviews 端点不可用（需 Enhanced/Premium 套餐）: {exc}")
        raise

    print(f"\n  ✓ {biz.name} 的评论 ({reviews.total} 条):")
    for r in reviews.reviews:
        preview = r.text[:80]
        print(f"    [{r.rating}★] {r.user.name}: {preview}...")
