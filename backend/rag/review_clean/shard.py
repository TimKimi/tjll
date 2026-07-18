"""分片、切片与进度文件。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


def stable_shard(business_id: str, modulus: int = 2) -> int:
    digest = hashlib.sha256(business_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulus


def filter_shard_ids(business_ids: Iterable[str], shard: int) -> list[str]:
    ids = sorted({bid for bid in business_ids if stable_shard(bid) == shard})
    return ids


def slice_ids(ids: list[str], start: int, end: int | None) -> list[str]:
    if start < 0:
        raise ValueError("--start 必须 >= 0")
    if end is None:
        end = len(ids)
    if end < start:
        raise ValueError("--end 必须 >= --start")
    return ids[start:end]


def progress_path(dataset_dir: Path, shard: int) -> Path:
    return dataset_dir / f"clean_progress_shard{shard}.json"


def load_progress(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    completed = data.get("completed", [])
    if not isinstance(completed, list):
        return set()
    return {str(item) for item in completed}


def save_progress(path: Path, completed: set[str], extra: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "completed": sorted(completed),
        "count": len(completed),
    }
    if extra:
        payload.update(extra)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def mark_completed(path: Path, business_id: str, extra: dict | None = None) -> set[str]:
    done = load_progress(path)
    done.add(business_id)
    save_progress(path, done, extra=extra)
    return done
