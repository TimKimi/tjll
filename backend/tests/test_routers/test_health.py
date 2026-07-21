"""健康检查路由的单元测试。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app


class TestHealthRoutes:
    """测试健康检查端点。"""

    def test_health_check(self):
        """测试 /health 接口返回正确的状态和数据。"""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "success"
        assert data["data"]["status"] == "ok"
        assert data["data"]["service"] == "TJLL API"

    def test_health_check_method_not_allowed(self):
        """测试非 GET 方法返回 405。"""
        client = TestClient(app)
        response = client.post("/health")
        assert response.status_code == 405

    def test_health_check_response_headers(self):
        """检查响应头。"""
        client = TestClient(app)
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]
