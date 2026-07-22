"""SectionInsight 单元测试（内存属性 + mock 入库/检索）。"""

from __future__ import annotations

import pytest


def test_section_insight_requires_section_id():
    from backend.llm.insight.section import SectionInsight

    with pytest.raises(ValueError, match="section_id"):
        SectionInsight("u1", "")


def test_add_facts_append_and_truncate_from_1based():
    from backend.llm.insight.section import SectionInsight

    s = SectionInsight("u1", "sec1")
    assert s.add_facts(items=["a", "b", "c", "d", "e"]) == ["a", "b", "c", "d", "e"]
    # 从第 4 条起删，再追加
    assert s.add_facts(start=4, items=["x", "y"]) == ["a", "b", "c", "x", "y"]
    # None 仅追加
    assert s.add_facts(items=["z"]) == ["a", "b", "c", "x", "y", "z"]


def test_add_facts_start_invalid():
    from backend.llm.insight.section import SectionInsight

    s = SectionInsight("u1", "sec1")
    with pytest.raises(ValueError, match="start"):
        s.add_facts(start=0, items=["a"])


def test_review_get_set():
    from backend.llm.insight.section import SectionInsight

    s = SectionInsight("u1", "sec1")
    assert s.get_review() == ""
    assert s.set_review("hello") == "hello"
    assert s.get_review() == "hello"


def test_batch_add_section_and_long_text():
    from backend.llm.insight.section import SectionInsight

    s = SectionInsight("u1", "sec1")
    out = s.batch_add_section({"预算": "200", "人数": "3"})
    assert out["预算"] == "200"
    text = s.to_section_long_text(size=800)
    assert "【预算】" in text
    assert "【人数】" in text
    # 父类 attrs 仍独立
    assert s.as_dict() == {}


def test_split_and_store_section_mock(monkeypatch):
    from backend.llm.insight import section as sec_mod
    from backend.llm.insight.section import SectionInsight

    calls: list[tuple] = []

    monkeypatch.setattr(
        sec_mod,
        "index_section_insight_chunks",
        lambda uuid, section_id, chunks, ensure=True: (
            calls.append((uuid, section_id, chunks)) or (len(chunks), [])
        ),
    )
    monkeypatch.setattr(
        sec_mod,
        "delete_section_insight_from_opensearch",
        lambda *a, **k: 0,
    )

    s = SectionInsight("u1", "secA")
    s.batch_add_section({"k": "v"})
    n = s.split_and_store_section()
    assert n >= 1
    assert calls and calls[0][0] == "u1" and calls[0][1] == "secA"
    assert s.last_section_chunk_size == n


def test_search_section_and_documents_delegate(monkeypatch):
    from backend.llm.insight import section as sec_mod
    from backend.llm.insight.section import SectionInsight

    monkeypatch.setattr(
        sec_mod,
        "search_section_insight_text",
        lambda q, uuid, section_id: f"attr:{q}:{uuid}:{section_id}",
    )
    monkeypatch.setattr(
        sec_mod,
        "search_section_document_texts",
        lambda q, uuid, section_id, filename=None, top_n=None: [
            f"doc:{q}:{filename}:{top_n}"
        ],
    )

    s = SectionInsight("u1", "sec1")
    assert s.search_section("你好") == "attr:你好:u1:sec1"
    assert s.search_documents("q", filename="a.md", top_n=2) == ["doc:q:a.md:2"]


def test_load_file_pipeline(tmp_path, monkeypatch):
    from backend.config.paths import REPO_ROOT
    from backend.llm.insight import section as sec_mod
    from backend.llm.insight.section import SectionInsight

    # 在仓库根下建临时相对路径文件
    rel_dir = tmp_path
    # 用 monkeypatch 让 resolve 指向 tmp：直接写绝对路径文件并用 to_repo 回退 name
    f = rel_dir / "note.md"
    f.write_text("hello world chunk", encoding="utf-8")

    indexed: list[dict] = []

    monkeypatch.setattr(
        sec_mod,
        "load_document_as_text",
        lambda p: "hello world chunk",
    )
    monkeypatch.setattr(sec_mod, "clean_text", lambda t: t)
    monkeypatch.setattr(
        sec_mod,
        "split_text_to_chunks",
        lambda text, chunk_size=None, chunk_overlap=None: ["hello", "world"],
    )
    monkeypatch.setattr(
        sec_mod,
        "index_section_document_chunks",
        lambda uuid, section_id, source_file, chunks, ensure=True: (
            indexed.append(
                {
                    "uuid": uuid,
                    "section_id": section_id,
                    "source_file": source_file,
                    "chunks": chunks,
                }
            )
            or (len(chunks), [])
        ),
    )
    monkeypatch.setattr(sec_mod, "resolve_repo_path", lambda p: f)
    monkeypatch.setattr(sec_mod, "to_repo_relative_posix", lambda p: "note.md")

    s = SectionInsight("u1", "sec1")
    out = s.load_file(str(f))
    assert out["chunks"] == 2
    assert out["source_file"] == "note.md"
    assert "note.md" in s.filenames()
    assert indexed[0]["chunks"] == ["hello", "world"]
    _ = REPO_ROOT  # 保持导入可用（路径约定）


def test_llm_tools_callable():
    from backend.llm.insight.section import SectionInsight

    s = SectionInsight("u1", "sec1")
    assert s.as_batch_add_section_tool().name == "batch_add_section_insight_attrs"
    assert s.as_add_facts_tool().name == "add_section_facts"
    assert s.as_set_review_tool().name == "set_section_review"
    s.as_batch_add_section_tool().invoke({"attrs": {"a": "1"}})
    assert s.section_as_dict()["a"] == "1"
    s.as_add_facts_tool().invoke({"items": ["f1"]})
    assert s.get_facts() == ["f1"]
    s.as_set_review_tool().invoke({"text": "rv"})
    assert s.get_review() == "rv"
