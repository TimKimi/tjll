"""index_cleaned_yelp 脚本单元测试（backfill / rewrite + 进度）。"""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from backend.rag.document.index_progress import (
    INDEX_PROGRESS_FILENAME,
    load_indexed_ids,
)


def _write_biz(cleaned: Path, bid: str, *, pos: str = "good", neg: str = "bad") -> None:
    (cleaned / f"{bid}.json").write_text(
        json.dumps(
            {
                "id": bid,
                "positive_summary": pos,
                "negative_summary": neg,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_run_index_missing_dir(tmp_path: Path):
    from backend.rag.scripts import index_cleaned_yelp as script

    args = Namespace(
        input_dir=str(tmp_path / "missing"),
        index="yelp_biz_v1",
        recreate=False,
        limit=None,
        mode="backfill",
    )
    try:
        script.run_index(args)
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError:
        pass


def test_backfill_skips_already_and_marks_complete(monkeypatch, tmp_path: Path):
    from backend.rag.scripts import index_cleaned_yelp as script

    cleaned = tmp_path / "cleaned"
    cleaned.mkdir()
    _write_biz(cleaned, "b1")
    _write_biz(cleaned, "b2")
    _write_biz(cleaned, "b3", pos="", neg="")

    progress = cleaned / INDEX_PROGRESS_FILENAME
    progress.write_text(
        json.dumps({"completed": ["b1"], "count": 1}, ensure_ascii=False),
        encoding="utf-8",
    )

    indexed: list[str] = []

    def fake_index(raw, *, index_name=None, ensure=False):
        bid = raw["id"]
        indexed.append(bid)
        if bid == "b2":
            return {
                "document_id": bid,
                "chunks": 2,
                "success": 2,
                "errors": [],
                "positive_chunks": 1,
                "negative_chunks": 1,
                "both_sides_complete": True,
            }
        return {
            "document_id": bid,
            "chunks": 0,
            "success": 0,
            "errors": [],
            "positive_chunks": 0,
            "negative_chunks": 0,
            "both_sides_complete": False,
        }

    monkeypatch.setattr(script, "ensure_index", lambda *a, **k: "idx")
    monkeypatch.setattr(script, "index_business_summaries_to_opensearch", fake_index)

    args = Namespace(
        input_dir=str(cleaned),
        index="yelp_biz_v1",
        recreate=False,
        limit=None,
        mode="backfill",
    )
    code = script.run_index(args)
    assert code == 0
    assert indexed == ["b2", "b3"]  # b1 skipped
    assert load_indexed_ids(progress) == {"b1", "b2"}


def test_backfill_does_not_mark_incomplete(monkeypatch, tmp_path: Path):
    from backend.rag.scripts import index_cleaned_yelp as script

    cleaned = tmp_path / "cleaned"
    cleaned.mkdir()
    _write_biz(cleaned, "only_pos", neg="")

    def fake_index(raw, *, index_name=None, ensure=False):
        return {
            "document_id": raw["id"],
            "chunks": 1,
            "success": 1,
            "errors": [],
            "positive_chunks": 1,
            "negative_chunks": 0,
            "both_sides_complete": False,
        }

    monkeypatch.setattr(script, "ensure_index", lambda *a, **k: "idx")
    monkeypatch.setattr(script, "index_business_summaries_to_opensearch", fake_index)

    args = Namespace(
        input_dir=str(cleaned),
        index="yelp_biz_v1",
        recreate=False,
        limit=None,
        mode="backfill",
    )
    assert script.run_index(args) == 0
    progress = cleaned / INDEX_PROGRESS_FILENAME
    assert not progress.exists() or load_indexed_ids(progress) == set()


def test_rewrite_clears_progress_and_reindexes_all(monkeypatch, tmp_path: Path):
    from backend.rag.scripts import index_cleaned_yelp as script

    cleaned = tmp_path / "cleaned"
    cleaned.mkdir()
    _write_biz(cleaned, "b1")
    _write_biz(cleaned, "b2")
    progress = cleaned / INDEX_PROGRESS_FILENAME
    progress.write_text(
        json.dumps({"completed": ["b1", "b2"], "count": 2}),
        encoding="utf-8",
    )

    indexed: list[str] = []
    ensure_calls: list[tuple] = []

    def fake_ensure(index_name=None, *, recreate=False):
        ensure_calls.append((index_name, recreate))
        return index_name

    def fake_index(raw, *, index_name=None, ensure=False):
        indexed.append(raw["id"])
        return {
            "document_id": raw["id"],
            "chunks": 2,
            "success": 2,
            "errors": [],
            "positive_chunks": 1,
            "negative_chunks": 1,
            "both_sides_complete": True,
        }

    monkeypatch.setattr(script, "ensure_index", fake_ensure)
    monkeypatch.setattr(script, "index_business_summaries_to_opensearch", fake_index)

    args = Namespace(
        input_dir=str(cleaned),
        index="yelp_biz_v1",
        recreate=False,
        limit=None,
        mode="rewrite",
    )
    code = script.run_index(args)
    assert code == 0
    assert ensure_calls == [("yelp_biz_v1", False)]
    assert set(indexed) == {"b1", "b2"}
    assert load_indexed_ids(progress) == {"b1", "b2"}


def test_main_rewrite_recreate_and_limit(monkeypatch, tmp_path: Path):
    from backend.rag.scripts import index_cleaned_yelp as script

    cleaned = tmp_path / "cleaned"
    cleaned.mkdir()
    for i in range(3):
        _write_biz(cleaned, f"b{i}")

    indexed: list[str] = []
    ensure_calls: list[tuple] = []

    def fake_ensure(index_name=None, *, recreate=False):
        ensure_calls.append((index_name, recreate))
        return index_name

    def fake_index(raw, **k):
        indexed.append(raw["id"])
        return {
            "document_id": raw["id"],
            "chunks": 2,
            "success": 2,
            "errors": [],
            "positive_chunks": 1,
            "negative_chunks": 1,
            "both_sides_complete": True,
        }

    monkeypatch.setattr(script, "ensure_index", fake_ensure)
    monkeypatch.setattr(script, "index_business_summaries_to_opensearch", fake_index)

    code = script.main(
        [
            "--input-dir",
            str(cleaned),
            "--mode",
            "rewrite",
            "--recreate",
            "--limit",
            "2",
        ]
    )
    assert code == 0
    assert ensure_calls == [(None, True)] or ensure_calls[0][1] is True
    assert len(indexed) == 2


def test_run_index_returns_1_on_bulk_errors(monkeypatch, tmp_path: Path):
    from backend.rag.scripts import index_cleaned_yelp as script

    cleaned = tmp_path / "cleaned"
    cleaned.mkdir()
    _write_biz(cleaned, "b1")

    monkeypatch.setattr(script, "ensure_index", lambda *a, **k: "idx")
    monkeypatch.setattr(
        script,
        "index_business_summaries_to_opensearch",
        lambda raw, **k: {
            "document_id": "b1",
            "chunks": 2,
            "success": 1,
            "errors": [{"e": 1}],
            "positive_chunks": 1,
            "negative_chunks": 1,
            "both_sides_complete": False,
        },
    )
    args = Namespace(
        input_dir=str(cleaned),
        index="yelp_biz_v1",
        recreate=False,
        limit=None,
        mode="backfill",
    )
    assert script.run_index(args) == 1
    assert load_indexed_ids(cleaned / INDEX_PROGRESS_FILENAME) == set()
