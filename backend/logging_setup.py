"""llm / rag 日志初始化：写入 config.log_dir（默认 backend/docs）。"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from backend.config import settings

_configured = False


def setup_app_logging(*, force: bool = False) -> None:
    """为 backend.llm / backend.rag 配置文件日志（不输出到控制台）。"""
    global _configured
    if _configured and not force:
        return

    log_dir = settings.log_dir_path
    log_dir.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, str(settings.log_level).upper(), logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    for name, filename in (
        ("backend.llm", "llm.log"),
        ("backend.rag", "rag.log"),
    ):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.handlers.clear()
        logger.propagate = False

        file_handler = RotatingFileHandler(
            log_dir / filename,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    _configured = True
