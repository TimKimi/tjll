"""日志初始化（向后兼容）—— 委托给 backend.core.logger。"""

from __future__ import annotations

from backend.core.logger import setup_app_logging

__all__ = ["setup_app_logging"]
