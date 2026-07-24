""" "TJLL 后端入口 —— FastAPI 统一入口。

启动方式：
    uv run uvicorn backend.main:app --reload

所有前端接口通过 /api/* 统一访问，包含：
  - 健康检查
  - 店铺（business）：列表、详情
  - 评论（review）：列表、详情
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.core.logger import setup_app_logging
from backend.core.schema import auto_adapt_schema
from backend.database import engine
from backend.models.base import Base
from backend.routers import admin as admin_router
from backend.routers import ai as ai_router
from backend.routers import auth as auth_router
from backend.routers import file as file_router
from backend.routers import business as business_router
from backend.routers import favorite as favorite_router
from backend.routers import health as health_router
from backend.routers import review as review_router
from backend.routers import user as user_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """应用生命周期：启动时建表，关闭时释放引擎。"""
    # 统一初始化日志（所有 backend.* 模块日志立即可用）
    setup_app_logging()

    if settings.APP_ENV == "development":
        await auto_adapt_schema(engine)
    else:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="TJLL API",
    description="大众点评 AI 智能助手后端服务 —— 统一接口入口",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

# ── CORS：允许前端跨域访问 ────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 静态文件（头像上传） ────────────────────────────────
_static_dir = Path(__file__).resolve().parent / "static"
_static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# ── 注册路由（统一入口） ──────────────────────────────────
app.include_router(health_router.router)
app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(business_router.router)
app.include_router(review_router.router)
app.include_router(ai_router.router)
app.include_router(favorite_router.router)
app.include_router(file_router.router)
app.include_router(admin_router.router)
