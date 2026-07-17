"""RAG 链结构单元测试（mock retriever / llm / redis）。"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda


def _fake_llm():
    """可接入 LCEL 的假 LLM：输入 prompt value，输出 AIMessage。"""

    def _call(messages):
        return AIMessage(content="模拟回答")

    return RunnableLambda(_call)


class _FakeRetriever:
    def __init__(self, docs=None):
        self.docs = docs or [
            Document(
                page_content="资料内容",
                metadata={"source_file": "a.pdf", "chunk_index": 0},
            )
        ]

    def invoke(self, query, config=None):
        return list(self.docs)


def test_format_docs():
    from backend.LLM.pipeline.context import format_docs

    docs = [
        Document(
            page_content="hello",
            metadata={"source_file": "x.pdf", "chunk_index": 1},
        )
    ]
    text = format_docs(docs)
    assert "hello" in text
    assert "x.pdf" in text
    assert "chunk#1" in text


def test_build_rag_chain_invoke(monkeypatch):
    import backend.LLM.pipeline.chains as chains_mod

    monkeypatch.setattr(
        chains_mod, "get_retriever", lambda mode="hybrid", k=10: _FakeRetriever()
    )
    monkeypatch.setattr(chains_mod, "get_llm", lambda temperature=0.2: _fake_llm())

    chain = chains_mod.build_rag_chain(k=3)
    result = chain.invoke("测试问题")
    assert result == "模拟回答"


def test_build_rag_chain_with_rerank(monkeypatch):
    import backend.LLM.pipeline.chains as chains_mod

    monkeypatch.setattr(
        chains_mod, "get_retriever", lambda mode="hybrid", k=10: _FakeRetriever()
    )
    monkeypatch.setattr(
        chains_mod,
        "rerank_docs",
        lambda query, docs, top_n=None: docs[: top_n or 1],
    )
    monkeypatch.setattr(chains_mod, "get_llm", lambda temperature=0.2: _fake_llm())

    chain = chains_mod.build_rag_chain_with_rerank(recall_k=5, top_n=1)
    result = chain.invoke("测试问题")
    assert result == "模拟回答"


def test_build_full_rag_chain_uses_session_id(monkeypatch):
    import backend.LLM.pipeline.chains as chains_mod
    from langchain_core.chat_history import InMemoryChatMessageHistory

    store: dict[str, InMemoryChatMessageHistory] = {}

    def fake_history(session_id: str):
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        return store[session_id]

    monkeypatch.setattr(chains_mod, "get_history", fake_history)
    monkeypatch.setattr(chains_mod, "get_llm", lambda temperature=0.2: _fake_llm())
    monkeypatch.setattr(
        chains_mod,
        "retrieve_rerank_context",
        lambda inputs: "假上下文",
    )

    chain = chains_mod.build_full_rag_chain()
    cfg: RunnableConfig = {"configurable": {"session_id": "sec-001"}}
    out = chain.invoke({"query": "你好"}, config=cfg)
    assert out == "模拟回答"
    assert "sec-001" in store
    assert len(store["sec-001"].messages) >= 2
