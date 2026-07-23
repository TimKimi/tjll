"""路由测试共享夹具：mock 数据库和认证依赖，避免连库。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.core.dependencies import get_current_user
from backend.database import get_db
from backend.main import app


@pytest.fixture
def client():
    """创建 TestClient，不进入 context manager 以跳过 lifespan。"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def auto_mock_deps():
    """自动 mock 数据库和认证依赖，避免请求时连库。

    默认 db.execute().scalar_one_or_none() 返回 None（"未找到"），
    各测试可按需调整 mock_db.execute.return_value 的返回值。
    """
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: {
        "sub": "u_test",
        "username": "测试用户",
    }
    yield
    app.dependency_overrides.clear()
