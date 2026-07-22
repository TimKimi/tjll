"""AI 路由集成测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch


class TestAIRoutes:
    """测试 AI 路由端点。"""

    # ── GET /api/ai/history ────────────────────────────────

    @patch("backend.routers.ai.get_ask_history")
    def test_get_history_success(self, mock_history, client):
        """获取历史成功。"""
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "uuid": "u_test",
            "section_id": "s1",
            "insight_create": False,
            "insight_use": False,
            "history": [],
        }
        mock_history.return_value = mock_result

        response = client.get(
            "/api/ai/history?uuid=u_test&section_id=s1",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["uuid"] == "u_test"

    def test_get_history_missing_param(self, client):
        """缺少参数应返回 422。"""
        response = client.get(
            "/api/ai/history?uuid=u_test",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 422

    # ── DELETE /api/ai/history ─────────────────────────────

    @patch("backend.routers.ai.delete_ask_history")
    def test_delete_history(self, mock_delete, client):
        """删除单条历史。"""
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "uuid": "u_test",
            "section_id": "s1",
            "deleted_sessions": 1,
            "section_ids": ["s1"],
        }
        mock_delete.return_value = mock_result

        response = client.delete(
            "/api/ai/history?uuid=u_test&section_id=s1",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200

    # ── DELETE /api/ai/histories ───────────────────────────

    @patch("backend.routers.ai.delete_ask_histories_by_uuid")
    def test_delete_histories(self, mock_delete, client):
        """删除全部历史。"""
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "uuid": "u_test",
            "section_id": None,
            "deleted_sessions": 2,
            "section_ids": ["s1", "s2"],
        }
        mock_delete.return_value = mock_result

        response = client.delete(
            "/api/ai/histories?uuid=u_test",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200

    # ── POST /api/ai/session/release ───────────────────────

    @patch("backend.routers.ai.release_ask_session")
    def test_release_session_single(self, mock_release, client):
        """释放单个会话槽。"""
        response = client.post(
            "/api/ai/session/release?uuid=u_test&section_id=s1",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200

    @patch("backend.routers.ai.release_ask_sessions_by_uuid")
    def test_release_session_all(self, mock_release, client):
        """释放全部会话槽。"""
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "uuid": "u_test",
            "released_sessions": 2,
            "section_ids": ["s1", "s2"],
        }
        mock_release.return_value = mock_result

        response = client.post(
            "/api/ai/session/release?uuid=u_test",
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200

    # ── POST /api/ai/ask (non-streaming) ───────────────────

    @patch("backend.routers.ai.LlmService")
    @patch("backend.routers.ai.llm_ask")
    def test_ask_non_stream(self, mock_ask, mock_service_class, client):
        """非流式 ask 返回 JSON。"""
        mock_service = MagicMock()
        mock_service.prepare_ask_request = AsyncMock(return_value=MagicMock())
        mock_service_class.return_value = mock_service

        mock_stream = MagicMock()
        mock_stream.__iter__.return_value = iter(["回复", "内容"])
        mock_stream.response = MagicMock()
        mock_stream.response.model_dump.return_value = {
            "query": "你好",
            "section_id": "s1",
            "uuid": "u_test",
            "answer": "回复内容",
            "query_filename": "",
            "sources": [],
        }
        mock_ask.return_value = mock_stream

        response = client.post(
            "/api/ai/ask",
            json={
                "query": "你好",
                "section_id": "s1",
                "stream": False,
            },
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["answer"] == "回复内容"
