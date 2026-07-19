"""应用自定义异常。"""

from __future__ import annotations


class AppError(Exception):
    """业务逻辑异常，携带 HTTP 状态码和错误消息。"""

    def __init__(self, message: str, code: int = 400) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
