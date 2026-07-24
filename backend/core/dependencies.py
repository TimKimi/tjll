"""FastAPI 依赖项：JWT 认证。"""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.online_tracker import tracker
from backend.core.security import decode_token

# Swagger UI Authorize 按钮
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """从 Authorization 头解析 JWT，返回当前用户信息。

    若 ``ONLINE_TRACKER_RESET_ON_STARTUP = True`` 且服务曾重启，
    重启前签发的 token 会被拒绝（通过 iat 字段判断）。

    Raises:
        HTTPException 401: token 缺失或无效。
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="未授权，请先登录")

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="token 无效或已过期")

    # 检查 token 签发时间是否在服务重置之后
    reset_iat = tracker.reset_iat
    if reset_iat > 0:
        token_iat = payload.get("iat")
        if token_iat is None or float(token_iat) < reset_iat:
            raise HTTPException(
                status_code=401,
                detail="token 已过期，请重新登录",
            )

    return payload
