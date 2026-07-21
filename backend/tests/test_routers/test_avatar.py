"""头像上传路由集成测试 + 压缩单元测试。"""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, patch

import pytest
from PIL import Image

from backend.core.exceptions import AppError
from backend.schemas.user import AvatarResponse
from backend.services.avatar import AvatarService


class TestAvatarRoutes:
    """测试头像上传端点。"""

    @patch("backend.routers.user.AvatarService")
    def test_upload_avatar_success(self, mock_service_class, client):
        """上传头像成功应返回 200 + 头像 URL。"""
        mock_instance = mock_service_class.return_value
        mock_instance.upload_avatar = AsyncMock(
            return_value=AvatarResponse(
                avatar="http://localhost:8000/static/avatars/u_test.jpg",
            )
        )
        file_content = io.BytesIO(b"fake_image_data")
        response = client.post(
            "/api/user/avatar",
            files={"avatar": ("test.jpg", file_content, "image/jpeg")},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "上传成功"
        assert data["data"]["avatar"].endswith(".jpg")

    @patch("backend.routers.user.AvatarService")
    def test_upload_avatar_invalid_type(self, mock_service_class, client):
        """不支持的图片格式应返回 400。"""
        mock_instance = mock_service_class.return_value
        mock_instance.upload_avatar = AsyncMock(
            side_effect=AppError("文件格式不支持", code=400)
        )
        file_content = io.BytesIO(b"fake_data")
        response = client.post(
            "/api/user/avatar",
            files={"avatar": ("test.txt", file_content, "text/plain")},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 400

    @patch("backend.routers.user.AvatarService")
    def test_upload_avatar_too_large(self, mock_service_class, client):
        """文件超过大小限制应返回 400。"""
        mock_instance = mock_service_class.return_value
        mock_instance.upload_avatar = AsyncMock(
            side_effect=AppError("文件大小超过限制（最大 2MB）", code=400)
        )
        file_content = io.BytesIO(b"x" * (2 * 1024 * 1024 + 1))
        response = client.post(
            "/api/user/avatar",
            files={"avatar": ("large.jpg", file_content, "image/jpeg")},
            headers={"Authorization": "Bearer test.token"},
        )
        assert response.status_code == 400

    def test_upload_avatar_requires_auth(self, client):
        """未认证请求应返回 401。"""
        from backend.core.dependencies import get_current_user
        from backend.main import app

        original_override = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            __import__("fastapi").HTTPException(
                status_code=401, detail="未授权，请先登录"
            )
        )

        file_content = io.BytesIO(b"fake_image_data")
        response = client.post(
            "/api/user/avatar",
            files={"avatar": ("test.jpg", file_content, "image/jpeg")},
        )
        assert response.status_code == 401

        if original_override is not None:
            app.dependency_overrides[get_current_user] = original_override
        else:
            del app.dependency_overrides[get_current_user]


class TestAvatarCompression:
    """测试头像压缩逻辑（_compress_image）。"""

    def _make_image(self, width: int, height: int, fmt: str = "RGB") -> bytes:
        """生成指定尺寸和模式的测试图片字节流。"""
        img = Image.new(fmt, (width, height), (255, 0, 0))
        buf = io.BytesIO()
        save_fmt = "JPEG" if fmt == "RGB" else "PNG"
        img.save(buf, format=save_fmt)
        return buf.getvalue()

    def test_compress_large_jpeg(self):
        """超过 512px 的大图应被缩放到 ≤512px。"""
        content = self._make_image(1024, 768)
        compressed = AvatarService._compress_image(content, ".jpg")
        result_img = Image.open(io.BytesIO(compressed))
        assert result_img.width <= 512
        assert result_img.height <= 512

    def test_compress_small_image_unchanged_dimensions(self):
        """小于 512px 的小图不应被放大。"""
        content = self._make_image(100, 80)
        compressed = AvatarService._compress_image(content, ".jpg")
        result_img = Image.open(io.BytesIO(compressed))
        assert result_img.width == 100
        assert result_img.height == 80

    def test_compress_rgba_png(self):
        """RGBA PNG 应被转为 RGB 保存。"""
        content = self._make_image(200, 200, fmt="RGBA")
        compressed = AvatarService._compress_image(content, ".png")
        result_img = Image.open(io.BytesIO(compressed))
        assert result_img.mode == "RGB"

    def test_compress_invalid_data_raises_error(self):
        """损坏的图片数据应抛出友好的 AppError。"""
        with pytest.raises(AppError, match="图片解码失败，请上传有效的图片文件"):
            AvatarService._compress_image(b"not_an_image", ".jpg")

    def test_compress_save_failure_raises_error(self):
        """能解码但无法重编码的图片应抛出友好错误。"""
        # 构造一个 PIL 可读取但 save 会失败的场景
        from unittest.mock import patch

        content = self._make_image(100, 100)
        with patch(
            "PIL.Image.Image.save",
            side_effect=OSError("cannot write mode"),
        ):
            with pytest.raises(AppError, match="图片处理失败，请上传有效的图片文件"):
                AvatarService._compress_image(content, ".jpg")

    def test_compress_result_smaller_than_original(self):
        """压缩后的文件大小应小于原始文件。"""
        # 创建一个较大的纯色图，JPEG 压缩效果明显
        content = self._make_image(800, 600)
        compressed = AvatarService._compress_image(content, ".jpg")
        assert len(compressed) < len(content)
