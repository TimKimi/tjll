"""index_progress 单元测试。"""

from __future__ import annotations

import json
from pathlib import Path

from backend.rag.document.index_progress import (
    INDEX_PROGRESS_FILENAME,
    both_sides_fully_indexed,
    clear_indexed,
    index_progress_path,
    list_business_json_files,
    load_indexed_ids,
    mark_indexed,
    save_indexed_ids,
)


def test_list_business_json_excludes_progress(tmp_path: Path):
    (tmp_path / "biz1.json").write_text("{}", encoding="utf-8")
    (tmp_path / INDEX_PROGRESS_FILENAME).write_text(
        json.dumps({"completed": ["x"]}),
        encoding="utf-8",
    )
    files = list_business_json_files(tmp_path)
    assert [p.name for p in files] == ["biz1.json"]


def test_progress_path_and_roundtrip(tmp_path: Path):
    path = index_progress_path(tmp_path)
    assert path.name == INDEX_PROGRESS_FILENAME
    assert load_indexed_ids(path) == set()

    save_indexed_ids(path, {"b2", "b1"})
    assert load_indexed_ids(path) == {"b1", "b2"}
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["count"] == 2
    assert data["completed"] == ["b1", "b2"]

    mark_indexed(path, "b3")
    assert load_indexed_ids(path) == {"b1", "b2", "b3"}

    clear_indexed(path)
    assert not path.exists()
    assert load_indexed_ids(path) == set()


def test_load_progress_invalid_completed(tmp_path: Path):
    path = tmp_path / INDEX_PROGRESS_FILENAME
    path.write_text(json.dumps({"completed": "bad"}), encoding="utf-8")
    assert load_indexed_ids(path) == set()


def test_both_sides_fully_indexed():
    assert both_sides_fully_indexed(
        {
            "chunks": 3,
            "success": 3,
            "errors": [],
            "positive_chunks": 2,
            "negative_chunks": 1,
        }
    )
    assert not both_sides_fully_indexed(
        {
            "chunks": 2,
            "success": 2,
            "errors": [],
            "positive_chunks": 2,
            "negative_chunks": 0,
        }
    )
    assert not both_sides_fully_indexed(
        {
            "chunks": 3,
            "success": 2,
            "errors": [],
            "positive_chunks": 2,
            "negative_chunks": 1,
        }
    )
    assert not both_sides_fully_indexed(
        {
            "chunks": 3,
            "success": 3,
            "errors": [{"item": 1}],
            "positive_chunks": 2,
            "negative_chunks": 1,
        }
    )
    assert not both_sides_fully_indexed({"chunks": 0, "success": 0, "errors": []})
