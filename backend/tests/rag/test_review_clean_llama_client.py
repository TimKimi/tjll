"""rag.review_clean.llama_client 单元测试（mock 子进程 / HTTP）。"""

from __future__ import annotations

from pathlib import Path

from backend.rag.review_clean.config import CleanLocalConfig
from backend.rag.review_clean.llama_client import LlamaServerClient


def _cfg(tmp_path: Path) -> CleanLocalConfig:
    server = tmp_path / "llama-server.exe"
    server.write_bytes(b"")
    model = tmp_path / "m.gguf"
    model.write_bytes(b"gguf")
    return CleanLocalConfig(
        model_dir=tmp_path,
        model_path=model,
        llama_cli=tmp_path / "cli.exe",
        llama_server=server,
        server_host="127.0.0.1",
        server_port=18080,
        n_ctx=512,
        n_gpu_layers=1,
        n_predict=32,
        extract_n_predict=16,
        prompt_reserve_tokens=100,
        target_chars=100,
    )


def test_chat_uses_http_when_already_started(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    client = LlamaServerClient(cfg)

    class FakeResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": " 回答 "}}]}

    class FakeHttp:
        def get(self, *_a, **_k):
            return FakeResp()

        def post(self, *_a, **_k):
            return FakeResp()

        def close(self):
            return None

    monkeypatch.setattr(client, "_client", FakeHttp())
    monkeypatch.setattr(client, "start", lambda: None)
    assert client.chat("sys", "user", max_tokens=8) == "回答"


def test_stop_noop_when_not_started(tmp_path):
    client = LlamaServerClient(_cfg(tmp_path))
    client.stop()  # should not raise
