"""异步数据库引擎与会话管理。

使用方式：
    from backend.database import async_session

    async with async_session() as session:
        ...
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=5,
    max_overflow=10,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():  # type: ignore[misc]
    """FastAPI 依赖注入用，获取数据库会话。

    Yields:
        AsyncSession: 数据库会话，FastAPI 依赖注入自动管理。
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
