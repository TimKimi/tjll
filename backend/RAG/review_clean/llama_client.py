"""通过 llama-server HTTP 调用本地 GGUF（启动一次、批内复用）。"""

from __future__ import annotations

import atexit
import logging
import subprocess
import time
from typing import Any

import httpx

from backend.RAG.review_clean.config import CleanLocalConfig

logger = logging.getLogger(__name__)
# 避免 httpx 在调用方未设置时刷屏
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class LlamaServerClient:
    """管理 llama-server 子进程并用 /v1/chat/completions 推理。"""

    def __init__(self, cfg: CleanLocalConfig) -> None:
        self.cfg = cfg
        self._proc: subprocess.Popen[bytes] | None = None
        self._base = f"http://{cfg.server_host}:{cfg.server_port}"
        self._client = httpx.Client(timeout=httpx.Timeout(600.0, connect=30.0))
        self._log_path = cfg.llama_server.parent / "llama-server.clean.log"
        self._log_fp: Any = None

    def start(self) -> None:
        if self._proc is not None:
            return
        cmd = [
            str(self.cfg.llama_server),
            "-m",
            str(self.cfg.model_path),
            "--host",
            self.cfg.server_host,
            "--port",
            str(self.cfg.server_port),
            "-c",
            str(self.cfg.n_ctx),
            "-ngl",
            str(self.cfg.n_gpu_layers),
            "-n",
            str(self.cfg.n_predict),
        ]
        logger.info("启动 llama-server: %s", " ".join(cmd))
        logger.info("llama-server 日志: %s", self._log_path)
        self._log_fp = self._log_path.open("wb")
        # 日志写文件，避免 PIPE 堵死；cwd=exe 目录以便加载 DLL
        self._proc = subprocess.Popen(
            cmd,
            cwd=str(self.cfg.llama_server.parent),
            stdout=self._log_fp,
            stderr=subprocess.STDOUT,
        )
        atexit.register(self.stop)
        # 加载 7B GGUF 到 GPU 可能需要一两分钟
        self._wait_ready(timeout_sec=300)

    def _model_ready(self) -> bool:
        """仅当模型真正可用时返回 True（忽略根路径 200）。"""
        try:
            h = self._client.get(f"{self._base}/health")
            if h.status_code == 200:
                return True
        except Exception:  # noqa: BLE001
            pass
        try:
            m = self._client.get(f"{self._base}/v1/models")
            if m.status_code == 200:
                return True
        except Exception:  # noqa: BLE001
            pass
        return False

    def _wait_ready(self, timeout_sec: int) -> None:
        deadline = time.time() + timeout_sec
        last_err: Exception | None = None
        last_status = ""
        while time.time() < deadline:
            if self._proc and self._proc.poll() is not None:
                raise RuntimeError(
                    f"llama-server 提前退出 (code={self._proc.returncode})。"
                    f"请查看日志: {self._log_path}"
                )
            try:
                h = self._client.get(f"{self._base}/health")
                last_status = f"/health->{h.status_code}"
                if h.status_code == 200:
                    logger.info("llama-server 已就绪 (%s)", last_status)
                    return
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                last_status = f"connect-error: {exc}"
            # 模型加载中会 503，继续等
            logger.info("等待模型加载… %s", last_status)
            time.sleep(2.0)
        raise TimeoutError(
            f"等待 llama-server 就绪超时 ({timeout_sec}s)。"
            f"最后状态: {last_status}；错误: {last_err}；日志: {self._log_path}"
        )

    def chat(self, system: str, user: str, *, max_tokens: int | None = None) -> str:
        self.start()
        body: dict[str, Any] = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.3,
            "max_tokens": max_tokens if max_tokens is not None else self.cfg.n_predict,
        }
        # 偶发仍在加载或短暂繁忙时重试
        deadline = time.time() + 180
        last_exc: Exception | None = None
        while time.time() < deadline:
            try:
                r = self._client.post(f"{self._base}/v1/chat/completions", json=body)
                if r.status_code == 503:
                    logger.info("chat 返回 503，等待模型…")
                    time.sleep(2.0)
                    continue
                r.raise_for_status()
                data = r.json()
                try:
                    return str(data["choices"][0]["message"]["content"]).strip()
                except (KeyError, IndexError, TypeError) as exc:
                    raise RuntimeError(f"无法解析 llama-server 响应: {data!r}") from exc
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response is not None and exc.response.status_code == 503:
                    time.sleep(2.0)
                    continue
                raise
            except httpx.HTTPError as exc:
                last_exc = exc
                time.sleep(2.0)
        raise RuntimeError(f"chat 多次重试仍失败: {last_exc}")

    def stop(self) -> None:
        if self._proc is None:
            return
        proc = self._proc
        self._proc = None
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        if self._log_fp is not None:
            try:
                self._log_fp.close()
            except Exception:  # noqa: BLE001
                pass
            self._log_fp = None
        self._client.close()
        logger.info("llama-server 已停止")

    def __enter__(self) -> LlamaServerClient:
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()
