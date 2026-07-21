"""头像上传业务逻辑层（含图片压缩）。"""

from __future__ import annotations

import io
import logging
import uuid
from pathlib import Path

from fastapi import UploadFile
from PIL import Image
from PIL.Image import Resampling
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.paths import PROJECT_ROOT
from backend.core.exceptions import AppError
from backend.models.app_user import AppUser
from backend.schemas.user import AvatarResponse

logger = logging.getLogger("backend.services.avatar")

# 允许的图片 MIME 类型
_ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif"}

# 允许的文件扩展名
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}

# 最大上传文件大小（2MB）
_MAX_FILE_SIZE = 2 * 1024 * 1024

# 压缩后最长边像素
_MAX_DIMENSION = 512

# JPEG 压缩质量（1-100）
_JPEG_QUALITY = 85

# 头像存储目录（相对 backend/）
_AVATAR_DIR = "static/avatars"


class AvatarService:
    """头像上传服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upload_avatar(self, user_id: str, file: UploadFile) -> AvatarResponse:
        """上传并压缩用户头像。"""
        # ── 校验 ──
        self._validate_file_type(file)

        ext = Path(file.filename or "").suffix.lower()

        content = await file.read()
        if len(content) > _MAX_FILE_SIZE:
            logger.warning("头像文件过大 user_id=%s size=%d", user_id, len(content))
            raise AppError("文件大小超过限制（最大 2MB）", code=400)

        # ── 压缩 ──
        compressed = self._compress_image(content, ext)

        # ── 确保目录存在 ──
        avatar_dir = PROJECT_ROOT / _AVATAR_DIR
        avatar_dir.mkdir(parents=True, exist_ok=True)

        # ── 写文件 ──
        unique_name = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = avatar_dir / unique_name
        file_path.write_bytes(compressed)

        # ── 更新 DB ──
        avatar_url = f"/static/avatars/{unique_name}"
        result = await self.db.execute(select(AppUser).where(AppUser.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.avatar = avatar_url
            await self.db.commit()

        logger.info(
            "头像上传成功 user_id=%s size=%d→%d", user_id, len(content), len(compressed)
        )
        return AvatarResponse(avatar=avatar_url)

    # ── 校验 ──────────────────────────────────────────────

    @staticmethod
    def _validate_file_type(file: UploadFile) -> None:
        """校验文件 MIME 类型和扩展名。"""
        if file.content_type not in _ALLOWED_MIME_TYPES:
            raise AppError("文件格式不支持", code=400)

        ext = Path(file.filename or "").suffix.lower()
        if ext not in _ALLOWED_EXTENSIONS:
            raise AppError("文件格式不支持", code=400)

    # ── 压缩 ──────────────────────────────────────────────

    @staticmethod
    def _compress_image(content: bytes, ext: str) -> bytes:
        """压缩图片：最长边 ≤512px + 质量优化。"""
        try:
            img = Image.open(io.BytesIO(content))
        except Exception as e:
            raise AppError("图片解码失败，请上传有效的图片文件", code=400) from e

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        if img.width > _MAX_DIMENSION or img.height > _MAX_DIMENSION:
            img.thumbnail((_MAX_DIMENSION, _MAX_DIMENSION), Resampling.LANCZOS)

        output = io.BytesIO()
        save_format = "JPEG" if ext in (".jpg", ".jpeg") else "PNG"
        try:
            if save_format == "JPEG":
                img.save(output, format="JPEG", quality=_JPEG_QUALITY, optimize=True)
            else:
                img.save(output, format="PNG", optimize=True)
        except Exception as e:
            raise AppError("图片处理失败，请上传有效的图片文件", code=400) from e

        return output.getvalue()
