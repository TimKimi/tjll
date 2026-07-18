"""cleaned 商家入库进度（仅双侧完整写入后记录）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

INDEX_PROGRESS_FILENAME = "index_progress.json"


def index_progress_path(cleaned_dir: Path) -> Path:
    return cleaned_dir / INDEX_PROGRESS_FILENAME


def list_business_json_files(cleaned_dir: Path) -> list[Path]:
    """列出 cleaned 下商家 JSON，排除进度文件。"""
    return sorted(
        p
        for p in cleaned_dir.glob("*.json")
        if p.name != INDEX_PROGRESS_FILENAME and p.is_file()
    )


def load_indexed_ids(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    completed = data.get("completed", [])
    if not isinstance(completed, list):
        return set()
    return {str(item) for item in completed}


def save_indexed_ids(path: Path, completed: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "completed": sorted(completed),
        "count": len(completed),
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def mark_indexed(path: Path, business_id: str) -> set[str]:
    done = load_indexed_ids(path)
    done.add(str(business_id))
    save_indexed_ids(path, done)
    return done


def clear_indexed(path: Path) -> None:
    """复写开始时可清空进度，再按完整入库结果重建。"""
    if path.is_file():
        path.unlink()


def both_sides_fully_indexed(result: dict[str, Any]) -> bool:
    """好评与坏评均成功写入（两侧均有 chunk、无错误、success 对齐）才算完整。"""
    errors = result.get("errors") or []
    if errors:
        return False
    chunks = int(result.get("chunks") or 0)
    success = int(result.get("success") or 0)
    if chunks <= 0 or success != chunks:
        return False
    pos = int(result.get("positive_chunks") or 0)
    neg = int(result.get("negative_chunks") or 0)
    return pos > 0 and neg > 0
