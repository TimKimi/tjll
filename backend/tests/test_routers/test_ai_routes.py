"""AI 路由核心对话测试。"""

from __future__ import annotations

from unittest.mock import patch

from backend.llm import AskInterruptResult, AskResult, AskStream


class TestAiAskRoute:
    """测试 /api/ai/ask 路由。"""

    # ── 情况 A：需要澄清 ──────────────────────────────

    @patch("backend.routers.ai.llm_ask")
    def test_ask_returns_interrupt(self, mock_ask, client):
        """ask 返回 AskInterruptResult 时应返回问卷 JSON。"""
        mock_ask.return_value = AskInterruptResult(
            uuid="u_test",
            section_id="s1",
            questions=[
                {
                    "question": "人均预算？",
                    "option": {"A": "100以内", "B": "100-300"},
                }
            ],  # type: ignore[arg-type]
        )
        response = client.post(
            "/api/ai/ask",
            json={"query": "推荐餐厅", "section_id": "s1", "stream": False},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "questions" in data["data"]
        assert data["data"]["questions"][0]["question"] == "人均预算？"

    # ── 情况 B：直接回答（流式） ──────────────────────

    @patch("backend.routers.ai.llm_ask")
    def test_ask_streaming(self, mock_ask, client):
        """ask 返回 AskStream 时应返回流式响应。"""
        holder: dict[str, AskResult | None] = {"response": None}
        stream = AskStream(iter(["你好", "世界"]), holder)
        mock_ask.return_value = stream

        response = client.post(
            "/api/ai/ask",
            json={"query": "你好", "section_id": "s1", "stream": True},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    # ── 情况 B：直接回答（非流式） ──────────────────────

    @patch("backend.routers.ai.llm_ask")
    def test_ask_non_stream(self, mock_ask, client):
        """ask 非流式应返回 JSON。"""
        result = AskResult(
            query="你好",
            section_id="s1",
            uuid="u_test",
            answer="世界",
            query_filename="",
        )
        holder: dict[str, AskResult | None] = {"response": result}
        stream = AskStream(iter(["世界"]), holder)
        mock_ask.return_value = stream

        response = client.post(
            "/api/ai/ask",
            json={"query": "你好", "section_id": "s1", "stream": False},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["answer"] == "世界"

    @patch("backend.routers.ai.llm_ask")
    def test_ask_non_stream_no_response(self, mock_ask, client):
        """非流式且 response 为 None 时应返回 500。"""
        holder: dict[str, AskResult | None] = {"response": None}
        stream = AskStream(iter(["text"]), holder)
        mock_ask.return_value = stream

        response = client.post(
            "/api/ai/ask",
            json={"query": "hi", "section_id": "s1", "stream": False},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 500

    # ── 认证 ──────────────────────────────────────────

    def test_ask_requires_auth(self, client):
        """未认证请求返回 401。"""
        from backend.core.dependencies import get_current_user
        from backend.main import app

        original = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            __import__("fastapi").HTTPException(status_code=401, detail="未授权")
        )
        try:
            response = client.post(
                "/api/ai/ask",
                json={"query": "hi", "section_id": "s1"},
            )
            assert response.status_code == 401
        finally:
            if original is not None:
                app.dependency_overrides[get_current_user] = original
            else:
                del app.dependency_overrides[get_current_user]


class TestAiAskInterruptRoute:
    """测试 /api/ai/ask/interrupt 路由。"""

    @patch("backend.routers.ai.submit_ask_interrupt")
    def test_submit_interrupt_returns_stream(self, mock_submit, client):
        """提交澄清答案应返回流式响应。"""
        result = AskResult(query="q", section_id="s1", uuid="u", answer="a")
        holder: dict[str, AskResult | None] = {"response": result}
        stream = AskStream(iter(["回答"]), holder)
        mock_submit.return_value = stream

        response = client.post(
            "/api/ai/ask/interrupt",
            json={
                "uuid": "u_test",
                "section_id": "s1",
                "answers": [{"question": "预算？", "result": "100-300"}],
            },
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    def test_submit_interrupt_requires_auth(self, client):
        """未认证请求返回 401。"""
        from backend.core.dependencies import get_current_user
        from backend.main import app

        original = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            __import__("fastapi").HTTPException(status_code=401, detail="未授权")
        )
        try:
            response = client.post(
                "/api/ai/ask/interrupt",
                json={"uuid": "u", "section_id": "s", "answers": []},
            )
            assert response.status_code == 401
        finally:
            if original is not None:
                app.dependency_overrides[get_current_user] = original
            else:
                del app.dependency_overrides[get_current_user]
