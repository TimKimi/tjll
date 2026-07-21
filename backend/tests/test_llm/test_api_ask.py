"""backend.llm.api.ask 门面单元测试（mock pipeline）。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.llm.api.schemas import AskRequest, AskResponse, HistoryMessage
from backend.llm.pipeline.rag_pipeline import RagAnswer


def test_ask_from_dict_maps_fields(monkeypatch):
    import backend.llm.api.handler as handler_mod

    def fake_pipeline(query: str, section_id: str) -> RagAnswer:
        assert query == "适合约会吗"
        assert section_id == "sec-1"
        return RagAnswer(
            answer="适合",
            query=query,
            section_id=section_id,
            sources=[
                {
                    "content": "服务很好",
                    "metadata": {
                        "name": "Acme",
                        "polarity": "positive",
                        "chunk_id": "b_pos_0000",
                        "score": 1.2,
                    },
                }
            ],
            history=[
                {"role": "user", "content": "上次问过"},
                {"role": "assistant", "content": "上次答过"},
            ],
        )

    monkeypatch.setattr(handler_mod, "answer_query_with_sources", fake_pipeline)

    from backend.llm import ask

    resp = ask(
        {
            "query": "适合约会吗",
            "section_id": "sec-1",
            "uuid": "req-9",
            "pdf": {"path": "/tmp/x.pdf"},
            "images": ["a.png"],
        }
    )
    assert isinstance(resp, AskResponse)
    assert resp.query == "适合约会吗"
    assert resp.section_id == "sec-1"
    assert resp.uuid == "req-9"
    assert resp.answer == "适合"
    assert len(resp.sources) == 1
    assert resp.sources[0].content == "服务很好"
    assert resp.sources[0].metadata["polarity"] == "positive"
    assert resp.sources[0].metadata["chunk_id"] == "b_pos_0000"
    assert len(resp.history) == 2
    assert resp.history[0] == HistoryMessage(role="user", content="上次问过")
    assert resp.history[1].role == "assistant"


def test_ask_from_model(monkeypatch):
    import backend.llm.api.handler as handler_mod

    monkeypatch.setattr(
        handler_mod,
        "answer_query_with_sources",
        lambda q, s: RagAnswer(
            answer="ok",
            query=q,
            section_id=s,
            sources=[],
            history=[],
        ),
    )
    from backend.llm.api import ask

    resp = ask(AskRequest(query="hi", section_id="s2", uuid=None))
    assert resp.answer == "ok"
    assert resp.uuid is None
    assert resp.sources == []
    assert resp.history == []


def test_ask_requires_query_and_section_id():
    with pytest.raises(ValidationError):
        AskRequest.model_validate({"query": "x"})
    with pytest.raises(ValidationError):
        AskRequest.model_validate({"section_id": "s"})
