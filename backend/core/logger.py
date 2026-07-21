"""统一日志管理器 — 接管所有 backend.* 模块的日志。"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from backend.config import settings

_configured = False

# 按模块划分的日志文件
_MODULE_LOG_FILES: dict[str, str] = {
    "backend.llm": "llm.log",
    "backend.rag": "rag.log",
    "backend.core": "core.log",
    "backend.data": "data.log",
    "backend.routers": "api.log",
    "backend.services": "api.log",
    "backend.schemas": "api.log",
    "backend.models": "db.log",
}

# 开发环境额外输出到控制台的模块前缀
_CONSOLE_NAMESPACES = [
    "backend.routers",
    "backend.services",
    "backend.core",
    "backend.llm.pipeline",
]


def setup_app_logging(*, force: bool = False) -> None:
    """配置所有 backend.* 模块的日志。

    - 按模块写入不同文件（自动轮转，每文件 5MB，保留 3 份）
    - 开发环境（APP_ENV=development）同时输出到控制台
    - 多次调用幂等（除非 force=True）
    """
    global _configured
    if _configured and not force:
        return
    _configured = True

    log_dir = settings.log_dir_path
    log_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, str(settings.log_level).upper(), logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    is_dev = settings.APP_ENV == "development"

    for module_name, filename in _MODULE_LOG_FILES.items():
        logger = logging.getLogger(module_name)
        logger.setLevel(level)
        logger.handlers.clear()
        logger.propagate = False

        # 文件 Handler
        file_handler = RotatingFileHandler(
            log_dir / filename,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

        # 控制台 Handler（仅开发环境）
        if is_dev and any(module_name.startswith(ns) for ns in _CONSOLE_NAMESPACES):
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(level)
            console.setFormatter(fmt)
            logger.addHandler(console)
