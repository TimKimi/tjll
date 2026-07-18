"""PDF 解析：MinerU → Markdown。"""

from __future__ import annotations

import os
from pathlib import Path

from backend.config import settings

# 必须在 import mineru 之前设置
os.environ.setdefault("MINERU_MODEL_SOURCE", settings.mineru_model_source)


def parse_pdf_with_mineru(
    pdf_path: str,
    output_dir: str | None = None,
) -> str:
    """用 MinerU 解析 PDF，返回生成的 Markdown 路径。"""
    try:
        import importlib

        mineru_common = importlib.import_module("mineru.cli.common")
        do_parse = mineru_common.do_parse
        read_fn = mineru_common.read_fn
    except ImportError as exc:
        raise ImportError(
            "未安装 mineru。请在 conda 环境 ai 中安装后再解析 PDF，"
            "或参考 models/README.md。"
        ) from exc

    pdf_path_p = Path(pdf_path)
    if not pdf_path_p.is_file():
        raise FileNotFoundError(f"PDF 不存在: {pdf_path_p}")

    out = Path(output_dir) if output_dir else Path(settings.mineru_output_dir)
    out.mkdir(parents=True, exist_ok=True)

    pdf_bytes = read_fn(pdf_path_p)
    do_parse(
        output_dir=str(out),
        pdf_file_names=[pdf_path_p.stem],
        pdf_bytes_list=[pdf_bytes],
        p_lang_list=["ch"],
        backend=settings.mineru_backend,
        parse_method=settings.mineru_method,
    )

    md_path = out / pdf_path_p.stem / "auto" / f"{pdf_path_p.stem}.md"
    if not md_path.exists():
        raise FileNotFoundError(
            f"MinerU 输出未找到: {md_path}。"
            f"请确认 ModelScope 缓存与流水线模型已就绪："
            f"{settings.mineru_pipeline_model_dir}"
        )
    return str(md_path)
