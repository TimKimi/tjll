"""DataService 集成测试。

依赖真实 PostgreSQL 数据库（需要 Docker 容器运行中）。

运行方式：
    docker compose up -d
    pytest backend/tests/data/test_service.py -v
"""

from __future__ import annotations

import pytest

from backend.data.service import DataService
from backend.models.business import Business
from backend.models.review import Review


@pytest.fixture
def svc():
    return DataService()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_business(svc, db_session):
    """查询商家。"""
    db_session.add(Business(id="b1", alias="b1", name="B1"))
    await db_session.flush()

    found = await svc.get_business("b1", session=db_session)
    assert found is not None
    assert found.name == "B1"

    nothing = await svc.get_business("no-such", session=db_session)
    assert nothing is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_businesses(svc, db_session):
    """商家列表搜索与过滤。"""
    for i in range(5):
        db_session.add(
            Business(
                id=f"b{i}",
                alias=f"b{i}",
                name=f"Biz {i}",
                rating=float(5 - i),
                review_count=i * 10,
            )
        )
    await db_session.flush()

    # 关键词
    r, t = await svc.list_businesses(keyword="Biz 0", session=db_session)
    assert t == 1
    assert r[0].id == "b0"

    # 评分过滤
    r, t = await svc.list_businesses(min_rating=3.0, session=db_session)
    assert t == 3

    # 分页 + 排序
    r, t = await svc.list_businesses(
        limit=3, sort_by="review_count", session=db_session
    )
    assert t == 5
    assert len(r) == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reviews(svc, db_session):
    """评论查询。"""
    db_session.add(Business(id="br", alias="br", name="Biz Rev"))
    db_session.add_all(
        [
            Review(
                id="r1",
                business_id="br",
                text="Good",
                rating=4,
                time_created="2020-01-01",
                url="https://example.com/1",
            ),
            Review(
                id="r2",
                business_id="br",
                text="Bad",
                rating=1,
                time_created="2020-01-02",
                url="https://example.com/2",
            ),
        ]
    )
    await db_session.flush()

    r, t = await svc.get_reviews_by_business("br", session=db_session)
    assert t == 2
    assert len(r) == 2

    r, t = await svc.get_reviews_by_business("no-such", session=db_session)
    assert t == 0

    found = await svc.get_review("r1", session=db_session)
    assert found is not None
    assert found.text == "Good"

    nf = await svc.get_review("no-such", session=db_session)
    assert nf is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_biz_with_reviews(svc, db_session):
    """商家及其评论（eager load）。"""
    db_session.add(Business(id="bwr", alias="bwr", name="WR"))
    db_session.add_all(
        [
            Review(
                id="wr1",
                business_id="bwr",
                text="R1",
                rating=5,
                time_created="2020-01-01",
                url="https://example.com/3",
            ),
            Review(
                id="wr2",
                business_id="bwr",
                text="R2",
                rating=3,
                time_created="2020-01-02",
                url="https://example.com/4",
            ),
        ]
    )
    await db_session.flush()

    result = await svc.get_business_with_reviews("bwr", session=db_session)
    assert result is not None
    assert result["business"]["name"] == "WR"
    assert len(result["reviews"]) == 2

    none_result = await svc.get_business_with_reviews("no-such", session=db_session)
    assert none_result is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stats(svc, db_session):
    """数据统计。"""
    db_session.add_all(
        [
            Business(id="s1", alias="s1", name="S1", rating=4.0),
            Business(id="s2", alias="s2", name="S2", rating=3.0, is_closed=True),
        ]
    )
    db_session.add_all(
        [
            Review(
                id="st1",
                business_id="s1",
                text="G",
                rating=4,
                time_created="2020-01-01",
                url="https://example.com/5",
            ),
            Review(
                id="st2",
                business_id="s2",
                text="B",
                rating=2,
                time_created="2020-01-02",
                url="https://example.com/6",
            ),
        ]
    )
    await db_session.flush()

    stats = await svc.get_stats(session=db_session)
    assert stats["businesses"] == 2
    assert stats["reviews"] >= 2
    assert stats["avg_rating"] > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rag_interfaces(svc, db_session):
    """RAG 使用的批量接口。"""
    db_session.add(Business(id="rag", alias="rag", name="RAG"))
    db_session.add_all(
        [
            Review(
                id="rg1",
                business_id="rag",
                text="Hello",
                rating=3,
                time_created="2020-01-01",
                url="https://example.com/7",
            ),
            Review(
                id="rg2",
                business_id="rag",
                text="World",
                rating=4,
                time_created="2020-01-02",
                url="https://example.com/8",
            ),
        ]
    )
    await db_session.flush()

    ids = await svc.get_all_business_ids(session=db_session)
    assert "rag" in ids

    texts = await svc.get_reviews_texts_by_business("rag", session=db_session)
    assert "Hello" in texts
    assert "World" in texts
