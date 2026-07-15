"""TJLL 后端入口 —— FastAPI 应用。

启动方式：
    uv run uvicorn backend.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.database import engine
from backend.models.base import Base


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """应用生命周期：启动时建表，关闭时释放引擎。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="TJLL API",
    description="TJLL 后端服务",
    version="0.1.0",
    lifespan=lifespan,
)


# ── 健康检查 ──────────────────────────────────────────────
@app.get("/health")
async def health() -> dict:
    """健康检查。"""
    return {"status": "ok"}
