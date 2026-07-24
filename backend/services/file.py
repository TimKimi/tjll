"""文件上传业务逻辑：校验、存储、防重名。"""

from __future__ import annotations

import logging
import mimetypes
from pathlib import Path

from fastapi import UploadFile

from backend.config import settings
from backend.core.exceptions import AppError

logger = logging.getLogger("backend.services.file")

# 允许的文件扩展名（用户需求：文本 / 图片 / PDF）
_ALLOWED_EXTENSIONS: set[str] = {
    ".md",
    ".txt",
    ".doc",
    ".docx",
    ".png",
    ".jpeg",
    ".jpg",
    ".pdf",
}

# 文件大小硬上限（代码级兜底，即使配置被误改也能防御）
_HARD_SIZE_LIMIT = 50 * 1024 * 1024  # 50MB


class FileService:
    """文件上传与清理服务。"""

    def __init__(self) -> None:
        self._static_dir = Path(__file__).resolve().parent.parent / "static"

    @staticmethod
    def _user_file_dir(username: str) -> Path:
        return Path(__file__).resolve().parent.parent / "static" / "file" / username

    @staticmethod
    def delete_session_files(username: str, section_id: str) -> None:
        """删除指定会话的上传文件目录。"""
        if not username or not section_id:
            return
        dir_path = FileService._user_file_dir(username) / section_id
        try:
            if dir_path.exists():
                import shutil

                shutil.rmtree(dir_path)
                logger.info("已删除会话附件: %s", dir_path)
        except OSError as e:
            logger.warning("删除会话附件失败: %s, %s", dir_path, e)

    @staticmethod
    def delete_all_user_files(username: str) -> None:
        """删除该用户所有上传文件。"""
        if not username:
            return
        dir_path = FileService._user_file_dir(username)
        try:
            if dir_path.exists():
                import shutil

                shutil.rmtree(dir_path)
                logger.info("已删除用户全部附件: %s", dir_path)
        except OSError as e:
            logger.warning("删除用户附件目录失败: %s, %s", dir_path, e)

    async def upload(self, file: UploadFile, user: dict, section_id: str) -> dict:
        """上传文件到当前会话并返回文件信息。

        Args:
            file: 上传的文件（FastAPI 的 UploadFile）。
            user: 当前用户 JWT payload（需包含 ``sub`` 和 ``username``）。
            section_id: 当前会话 ID，与 AI 对话的 ``section_id`` 对应。

        Returns:
            dict: {filename, url, size, mime_type}

        Raises:
            AppError: 文件类型不允许、大小超限、重名等。
        """
        # ── 1. 校验文件扩展名 ──────────────────────────────
        original_name = file.filename or ""
        # 只取文件名部分，去掉路径成分（防路径穿越）
        safe_name = Path(original_name).name
        if not safe_name:
            raise AppError("文件名不能为空", code=400)

        ext = Path(safe_name).suffix.lower()
        if ext not in _ALLOWED_EXTENSIONS:
            logger.warning("不允许的文件类型: %s (ext=%s)", safe_name, ext)
            raise AppError(f"不支持的文件类型「{ext}」，仅支持文本/图片/PDF", code=400)

        # ── 2. 校验 MIME type（后端自己判断，不信任请求头）──
        guessed_type, _ = mimetypes.guess_type(safe_name)
        if guessed_type:
            _validate_mime(guessed_type, ext)

        # 读取前 16 字节用于 magic bytes 检测
        contents = await file.read(16)
        await file.seek(0)

        if not _validate_magic_bytes(contents, ext):
            raise AppError("文件内容与扩展名不匹配", code=400)

        # ── 3. 校验文件大小 ──────────────────────────────
        file.file.seek(0, 2)  # 移到文件末尾
        size = file.file.tell()
        file.file.seek(0)  # 回到开头

        if size > _HARD_SIZE_LIMIT:
            raise AppError("文件过大，最大允许 50MB", code=400)
        if size > settings.FILE_MAX_SIZE:
            raise AppError(
                f"文件过大，当前限制 {settings.FILE_MAX_SIZE // (1024 * 1024)}MB",
                code=400,
            )

        # ── 4. 构建存储路径（static/file/{username}/{section_id}/）────
        username = user.get("username", "unknown")
        user_dir = self._static_dir / "file" / username / section_id
        user_dir.mkdir(parents=True, exist_ok=True)

        dest = user_dir / safe_name
        if dest.exists():
            raise AppError(f"文件「{safe_name}」已存在，请重命名后上传", code=409)

        # ── 5. 写入文件 ──────────────────────────────────
        content = await file.read()
        dest.write_bytes(content)

        file_size = len(content)
        logger.info(
            "文件上传成功 user=%s section_id=%s name=%s size=%d",
            username,
            section_id,
            safe_name,
            file_size,
        )

        return {
            "filename": safe_name,
            "url": f"/static/file/{username}/{section_id}/{safe_name}",
            "size": file_size,
            "mime_type": guessed_type or "application/octet-stream",
        }


def _validate_mime(mime: str, ext: str) -> None:
    """校验 MIME 类型与扩展名是否匹配（防前端伪造 Content-Type）。"""
    text_exts = {".md", ".txt"}
    image_exts = {".png", ".jpg", ".jpeg"}

    if ext in text_exts and not mime.startswith("text/"):
        raise AppError("文件类型不匹配", code=400)
    if ext in image_exts and not mime.startswith("image/"):
        raise AppError("文件类型不匹配", code=400)
    if ext == ".pdf" and mime != "application/pdf":
        raise AppError("文件类型不匹配", code=400)
    if ext == ".doc" and mime != "application/msword":
        raise AppError("文件类型不匹配", code=400)
    if ext == ".docx" and mime not in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        raise AppError("文件类型不匹配", code=400)


def _validate_magic_bytes(data: bytes, ext: str) -> bool:
    """通过文件头魔数二次校验文件真实性。

    仅对有固定魔数的格式做校验；
    .md / .txt / .doc / .docx 没有魔数，跳过。
    """
    if ext == ".png":
        return data[:8] == b"\x89PNG\r\n\x1a\n"
    if ext in (".jpg", ".jpeg"):
        return data[:3] == b"\xff\xd8\xff"
    if ext == ".pdf":
        return data[:5] == b"%PDF-"
    return True
