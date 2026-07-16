"""pytest 共享夹具 — 数据库会话管理。"""

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


@pytest_asyncio.fixture(scope="function")
async def create_tables():
    """确保表存在并清空旧数据。"""
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
        logger.info("[setup] truncating...")
        await conn.execute(text("TRUNCATE TABLE businesses CASCADE"))
        await conn.execute(text("TRUNCATE TABLE reviews CASCADE"))
        logger.info("[setup] ddl done")
    logger.info("[setup] dispose engine...")
    await engine.dispose()
    logger.info("[setup] done (%.2fs)", time.monotonic() - t0)


@pytest_asyncio.fixture
async def db_session(create_tables) -> AsyncGenerator[AsyncSession, None]:
    """Get db session, rollback after test."""
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
        logger.info("[session] ready (%.2fs)", time.monotonic() - t0)
        try:
            yield session
            logger.info("[session] test done, cleanup...")
        finally:
            logger.info("[session] rollback...")
            await session.rollback()
            logger.info("[session] close session...")
    logger.info("[session] dispose engine...")
    await engine.dispose()
    logger.info("[session] engine disposed")
