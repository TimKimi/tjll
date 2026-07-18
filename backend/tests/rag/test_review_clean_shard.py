"""rag.review_clean.shard 单元测试。"""

from __future__ import annotations

import pytest

from backend.rag.review_clean.shard import (
    filter_shard_ids,
    load_progress,
    mark_completed,
    progress_path,
    save_progress,
    slice_ids,
    stable_shard,
)


def test_stable_shard_deterministic():
    assert stable_shard("biz-1", modulus=2) == stable_shard("biz-1", modulus=2)
    assert stable_shard("biz-1", modulus=2) in (0, 1)


def test_filter_shard_ids():
    ids = ["a", "b", "c", "a"]
    shard0 = filter_shard_ids(ids, 0)
    shard1 = filter_shard_ids(ids, 1)
    assert set(shard0) | set(shard1) == {"a", "b", "c"}
    assert set(shard0) & set(shard1) == set()


def test_slice_ids():
    assert slice_ids(["a", "b", "c", "d"], 1, 3) == ["b", "c"]
    assert slice_ids(["a", "b"], 0, None) == ["a", "b"]
    with pytest.raises(ValueError, match="start"):
        slice_ids(["a"], -1, 1)
    with pytest.raises(ValueError, match="end"):
        slice_ids(["a", "b"], 2, 1)


def test_progress_roundtrip(tmp_path):
    path = progress_path(tmp_path, shard=0)
    assert path.name == "clean_progress_shard0.json"
    assert load_progress(path) == set()

    save_progress(path, {"b1", "b2"}, extra={"note": "x"})
    loaded = load_progress(path)
    assert loaded == {"b1", "b2"}

    done = mark_completed(path, "b3")
    assert "b3" in done
    assert load_progress(path) == {"b1", "b2", "b3"}
