"""MinerU 配置 — PDF 解析、ModelScope 模型。"""

from __future__ import annotations

from pathlib import Path

from backend.config.paths import resolve_path


class MineruMixin:
    """MinerU PDF 解析 + ModelScope 模型配置。

    所有默认值在此统一修改。
    """

    # ── ModelScope ───────────────────────────────────────────
    # 模型来源：modelscope / huggingface
    mineru_model_source: str = "modelscope"
    # ModelScope 缓存目录（空则用默认缓存路径）
    modelscope_cache_path: str = ""

    # ── MinerU 模型路径（相对 modelscope_cache_path）──
    # PDF-Extract-Kit 管道模型
    mineru_pipeline_model_path: str = (
        "models/OpenDataLab--PDF-Extract-Kit-1.0/snapshots/master"
    )
    # MinerU VLM 模型
    mineru_vlm_model_path: str = (
        "models/OpenDataLab--MinerU2.5-Pro-2605-1.2B/snapshots/master"
    )

    # ── MinerU 运行参数 ───────────────────────────────────────
    # 后端：pipeline / vlm
    mineru_backend: str = "pipeline"
    # 解析方法：auto / pdf / image
    mineru_method: str = "auto"

    # ── 数据目录（相对 backend/）──
    # MinerU 解析结果输出目录
    mineru_output_path: str = "data/mineru-output"
    # PDF 源文件目录
    pdfs_path: str = "data/pdfs"

    # ── 派生属性 ─────────────────────────────────────────────

    @property
    def modelscope_cache_dir(self) -> str:
        """ModelScope 缓存绝对路径。"""
        return resolve_path(self.modelscope_cache_path)

    @property
    def mineru_pipeline_model_dir(self) -> str:
        """管道模型绝对路径。"""
        base = Path(self.modelscope_cache_dir)
        rel = Path(self.mineru_pipeline_model_path)
        if rel.is_absolute():
            return str(rel.resolve())
        return str((base / rel).resolve())

    @property
    def mineru_vlm_model_dir(self) -> str:
        """VLM 模型绝对路径。"""
        base = Path(self.modelscope_cache_dir)
        rel = Path(self.mineru_vlm_model_path)
        if rel.is_absolute():
            return str(rel.resolve())
        return str((base / rel).resolve())

    @property
    def mineru_output_dir(self) -> str:
        """MinerU 输出绝对路径。"""
        return resolve_path(self.mineru_output_path)

    @property
    def pdfs_dir(self) -> str:
        """PDF 源文件绝对路径。"""
        return resolve_path(self.pdfs_path)
