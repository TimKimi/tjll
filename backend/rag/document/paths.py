"""仓库相对路径解析与文档后缀约定。"""

from __future__ import annotations

import logging
from pathlib import Path

from backend.config.paths import REPO_ROOT

logger = logging.getLogger("backend.rag.document.paths")

_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}

SUPPORTED_EXTS: set[str] = {
    ".pdf",
    ".md",
    ".txt",
    ".doc",
    ".docx",
    *_IMAGE_EXTS,
}

__all__ = [
    "SUPPORTED_EXTS",
    "normalize_backend_path",
    "resolve_repo_path",
    "to_repo_relative_posix",
]


def resolve_repo_path(file_path: str) -> Path:
    """相对 tjll 仓库根解析为绝对路径；已是绝对路径则直接 resolve。"""
    text = (file_path or "").strip().replace("\\", "/")
    if text.startswith("./"):
        text = text[2:]
    p = Path(text)
    if p.is_absolute():
        return p.resolve()
    return (REPO_ROOT / p).resolve()


def to_repo_relative_posix(path: Path) -> str:
    """转为相对仓库根的 POSIX 路径（无 ./ 前缀）；失败返回 name。"""
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def normalize_backend_path(file_path: str) -> str | None:
    """强制规范为 ``./backend/.../name.ext``；非法返回 None。"""
    text = (file_path or "").strip().replace("\\", "/")
    if not text:
        return None
    try:
        abs_path = resolve_repo_path(text)
        rel = abs_path.relative_to(REPO_ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        logger.warning("normalize_backend_path failed path=%r", file_path)
        return None
    if ".." in Path(rel).parts:
        logger.warning("normalize_backend_path traversal path=%r", file_path)
        return None
    if not rel.startswith("backend/"):
        logger.warning(
            "normalize_backend_path not under backend/ path=%r rel=%r",
            file_path,
            rel,
        )
        return None
    return f"./{rel}"
