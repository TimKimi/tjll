"""读取旁路 config.local.toml（不写根 .env）。"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "qwen2.5-7b-instruct-gguf"
CONFIG_NAME = "config.local.toml"
EXAMPLE_NAME = "config.local.example.toml"


@dataclass(frozen=True)
class CleanLocalConfig:
    model_dir: Path
    model_path: Path
    llama_cli: Path
    llama_server: Path
    server_host: str
    server_port: int
    n_ctx: int
    n_gpu_layers: int
    n_predict: int
    extract_n_predict: int
    prompt_reserve_tokens: int
    target_chars: int

    @property
    def input_char_budget(self) -> int:
        """可用于塞评论的近似字符预算。"""
        tokens = max(
            256,
            self.n_ctx - self.prompt_reserve_tokens - self.extract_n_predict,
        )
        # 中英混合保守：约 2 字符/token
        return tokens * 2


def load_clean_config(model_dir: Path | None = None) -> CleanLocalConfig:
    base = model_dir or MODEL_DIR
    cfg_path = base / CONFIG_NAME
    if not cfg_path.is_file():
        raise FileNotFoundError(
            f"缺少旁路配置 {cfg_path}。请复制 {EXAMPLE_NAME} 为 {CONFIG_NAME}，"
            "并确保已下载 GGUF / llama.cpp（见该目录 README）。"
            "不要写入仓库根 .env。"
        )

    with cfg_path.open("rb") as f:
        raw = tomllib.load(f)

    def _resolve(key: str, default: str | None = None) -> Path:
        rel = raw.get(key, default)
        if not rel:
            raise KeyError(f"config.local.toml 缺少字段: {key}")
        p = Path(str(rel))
        return p if p.is_absolute() else (base / p).resolve()

    model_path = _resolve("model_path")
    llama_cli = _resolve("llama_cli")
    llama_server = _resolve(
        "llama_server",
        default=str(Path("../../tools/llama.cpp/llama-server.exe")),
    )

    if not model_path.is_file():
        raise FileNotFoundError(f"GGUF 不存在: {model_path}")
    if not llama_server.is_file():
        raise FileNotFoundError(
            f"llama-server 不存在: {llama_server}\n"
            "请按 backend/rag/tools/llama.cpp/README.md 解压 CUDA 预编译包。"
        )

    return CleanLocalConfig(
        model_dir=base,
        model_path=model_path,
        llama_cli=llama_cli,
        llama_server=llama_server,
        server_host=str(raw.get("server_host", "127.0.0.1")),
        server_port=int(raw.get("server_port", 18080)),
        n_ctx=int(raw.get("n_ctx", 4096)),
        n_gpu_layers=int(raw.get("n_gpu_layers", 99)),
        n_predict=int(raw.get("n_predict", 1024)),
        extract_n_predict=int(raw.get("extract_n_predict", 256)),
        prompt_reserve_tokens=int(raw.get("prompt_reserve_tokens", 600)),
        target_chars=int(raw.get("target_chars", 800)),
    )
