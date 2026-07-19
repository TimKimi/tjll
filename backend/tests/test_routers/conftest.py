"""路由测试共享夹具：mock 数据库和认证依赖，避免连库。"""

from __future__ import annotations

from unittest.mock import AsyncMock

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
    """自动 mock 数据库和认证依赖，避免请求时连库。"""
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: {
        "sub": "u_test",
        "username": "测试用户",
    }
    yield
    app.dependency_overrides.clear()
