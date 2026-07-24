"""文件上传路由测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from backend.schemas.ai import FileUploadResponse


class TestFileUploadRoutes:
    """测试文件上传路由。"""

    @patch("backend.routers.file.FileService")
    def test_upload_success(self, mock_service_class, client):
        """上传成功应返回文件信息。"""
        mock_instance = mock_service_class.return_value
        mock_instance.upload = AsyncMock(
            return_value={
                "filename": "test.md",
                "url": "./backend/static/file/user/sid/test.md",
                "size": 100,
                "mime_type": "text/markdown",
            }
        )

        response = client.post(
            "/api/file/upload?section_id=sid",
            files={"file": ("test.md", b"# Hello", "text/markdown")},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["filename"] == "test.md"
        assert data["data"]["url"].startswith("./backend/static/file/")

    @patch("backend.routers.file.FileService")
    def test_upload_requires_auth(self, mock_service_class, client):
        """未认证请求返回 401。"""
        from backend.core.dependencies import get_current_user
        from backend.main import app

        original = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            __import__("fastapi").HTTPException(status_code=401, detail="未授权")
        )
        try:
            response = client.post(
                "/api/file/upload?section_id=sid",
                files={"file": ("test.md", b"# Hello", "text/markdown")},
            )
            assert response.status_code == 401
        finally:
            if original is not None:
                app.dependency_overrides[get_current_user] = original
            else:
                del app.dependency_overrides[get_current_user]

    def test_upload_response_schema(self):
        """FileUploadResponse 序列化正确。"""
        resp = FileUploadResponse(
            filename="test.docx",
            url="./backend/static/file/user/sid/test.docx",
            size=2048,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        data = resp.model_dump()
        assert data["filename"] == "test.docx"
        assert data["url"].startswith("./backend/static/file/")
        assert data["size"] == 2048
