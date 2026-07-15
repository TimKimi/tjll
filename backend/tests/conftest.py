"""pytest 共享夹具 — 数据库会话管理。"""

from __future__ import annotations

from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import async_session, engine
from backend.models.base import Base


@pytest_asyncio.fixture(scope="session")
async def create_tables():
    """确保数据库表存在（整个测试会话只执行一次）。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 不 drop 表，避免影响其他开发者


@pytest_asyncio.fixture
async def db_session(create_tables) -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话，测试结束后回滚事务。"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()
