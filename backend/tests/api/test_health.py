# backend/tests/api/test_health.py
"""健康检查路由的单元测试。"""

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

        # 验证响应结构符合 ApiResponse
        assert "code" in data
        assert "message" in data
        assert "data" in data
        assert data["code"] == 0
        assert data["message"] == "success"

        # 验证 data 内容
        assert data["data"]["status"] == "ok"
        assert data["data"]["service"] == "TJLL API"

    def test_health_check_method_not_allowed(self):
        """测试非 GET 方法返回 405。"""
        client = TestClient(app)
        response = client.post("/health")
        assert response.status_code == 405

    def test_health_check_response_headers(self):
        """检查响应头（可选）。"""
        client = TestClient(app)
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]
