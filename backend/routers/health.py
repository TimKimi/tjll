"""健康检查路由。"""

from __future__ import annotations

from fastapi import APIRouter

from backend.schemas.common import ApiResponse

router = APIRouter(tags=["健康检查"])


@router.get("/health", summary="健康检查")
async def health_check() -> ApiResponse[dict]:
    """服务健康检查接口，用于前端连通性验证。"""
    return ApiResponse.ok(
        data={
            "status": "ok",
            "service": "TJLL API",
        }
    )
