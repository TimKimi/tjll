"""应用配置，从环境变量读取配置项。

使用方式：
    from backend.config import settings
    settings.xxx
"""

from os import environ


class Settings:
    """全局配置，所有配置项集中在此。

    新增配置项时在此类中添加属性即可，统一管理。
    """

    # ── 服务器 ─────────────────────────────────────────────
    APP_HOST: str = environ.get("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(environ.get("APP_PORT", "8000"))


settings = Settings()
