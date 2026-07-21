"""pytest 共享夹具 — 数据库会话管理。

注意：数据清理使用 DELETE 而非 TRUNCATE，且与测试数据在同一事务内。
事务始终 rollback，因此各 xdist worker 的数据完全隔离，可安全并行。
"""

from __future__ import annotations

import logging
import time
from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import settings
from backend.models.base import Base

logger = logging.getLogger("tests.conftest")

# 按 FK 依赖顺序排列，避免 DELETE 时违反外键约束
_TABLES_TO_CLEAN = [
    "favorites",
    "reviews",
    "businesses",
    "app_users",
    "users",
]


@pytest_asyncio.fixture(scope="function")
async def create_tables():
    """确保表存在（不做数据清理，由 db_session 的 rollback 控制）。"""
    t0 = time.monotonic()
    logger.info("[setup] create engine...")
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=1,
        max_overflow=0,
    )
    logger.info("[setup] engine.begin()...")
    async with engine.begin() as conn:
        logger.info("[setup] create_all...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("[setup] ddl done")
    logger.info("[setup] dispose engine...")
    await engine.dispose()
    logger.info("[setup] done (%.2fs)", time.monotonic() - t0)


@pytest_asyncio.fixture
async def db_session(create_tables) -> AsyncGenerator[AsyncSession, None]:
    """Get db session, clean data in transaction, rollback after test.

    清理 DELETE 与测试数据在同一个未提交的事务中，
    最终的 rollback() 会撤销所有更改，不残留任何数据。
    不同 xdist worker 的事务互相隔离，可安全并行执行。
    """
    t0 = time.monotonic()
    logger.info("[session] create engine...")
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=2,
        max_overflow=0,
    )
    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    logger.info("[session] create session...")
    async with factory() as session:
        # 清理旧数据 — 与后续测试操作在同一事务内，最终被 rollback
        for table in _TABLES_TO_CLEAN:
            await session.execute(text(f"DELETE FROM {table}"))
        logger.info("[session] ready (%.2fs)", time.monotonic() - t0)
        try:
            yield session
            logger.info("[session] test done, rollback...")
        finally:
            await session.rollback()
            logger.info("[session] close session...")
    logger.info("[session] dispose engine...")
    await engine.dispose()
    logger.info("[session] engine disposed")
