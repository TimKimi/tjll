"""仓库相对路径解析与文档后缀约定。"""

from __future__ import annotations

from pathlib import Path

from backend.config.paths import REPO_ROOT

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
    "resolve_repo_path",
    "to_repo_relative_posix",
]


def resolve_repo_path(file_path: str) -> Path:
    """相对 tjll 仓库根解析为绝对路径；已是绝对路径则直接 resolve。"""
    p = Path(file_path)
    if p.is_absolute():
        return p.resolve()
    return (REPO_ROOT / p).resolve()


def to_repo_relative_posix(path: Path) -> str:
    """尽量转为相对仓库根的 POSIX 路径；否则返回 name。"""
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.name
