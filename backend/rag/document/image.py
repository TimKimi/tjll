"""图片解析：转单页 PDF 后走 MinerU，得到带结构的 Markdown 纯文本。"""

from __future__ import annotations

import tempfile
from pathlib import Path

from backend.rag.document.pdf import parse_pdf_with_mineru


def image_to_single_page_pdf(image_path: str, pdf_path: str) -> str:
    """将 png/jpg/jpeg 写入单页 PDF，返回 pdf_path。"""
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError("解析图片需要 Pillow。请安装 pillow 后再试。") from exc

    src = Path(image_path)
    if not src.is_file():
        raise FileNotFoundError(f"图片不存在: {src}")

    out = Path(pdf_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(src) as img:
        rgb = img.convert("RGB")
        rgb.save(out, "PDF", resolution=100.0)
    return str(out)


def parse_image_with_mineru(
    image_path: str,
    output_dir: str | None = None,
) -> str:
    """图片 → 临时单页 PDF → MinerU → 返回 Markdown 文件路径。"""
    with tempfile.TemporaryDirectory(prefix="section_img_") as tmp:
        pdf_path = Path(tmp) / f"{Path(image_path).stem}.pdf"
        image_to_single_page_pdf(image_path, str(pdf_path))
        return parse_pdf_with_mineru(str(pdf_path), output_dir=output_dir)
