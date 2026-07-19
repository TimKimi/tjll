"""FastAPI 依赖项：JWT 认证。"""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.security import decode_token

# Swagger UI Authorize 按钮
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """从 Authorization 头解析 JWT，返回当前用户信息。

    Raises:
        HTTPException 401: token 缺失或无效。
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="未授权，请先登录")

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="token 无效或已过期")

    return payload
