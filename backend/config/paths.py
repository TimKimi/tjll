"""路径工具 — 项目根目录、相对路径解析。"""

from __future__ import annotations

from pathlib import Path

# backend/config/paths.py → backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# backend/ → 仓库根目录
REPO_ROOT = PROJECT_ROOT.parent


def resolve_path(path: str) -> str:
    """将相对 ``backend/`` 的路径解析为绝对路径。"""
    p = Path(path)
    if p.is_absolute():
        return str(p.resolve())
    return str((PROJECT_ROOT / p).resolve())
