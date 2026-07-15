"""TJLL 后端入口 —— FastAPI 应用。

启动方式：
    uv run uvicorn backend.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="TJLL API",
    description="TJLL 后端服务",
    version="0.1.0",
)


# ── 健康检查 ──────────────────────────────────────────────
@app.get("/health")
async def health() -> dict:
    """健康检查。"""
    return {"status": "ok"}
