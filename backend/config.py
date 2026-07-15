"""应用配置，从环境变量 + .env 文件读取配置项。

使用方式：
    from backend.config import settings
    settings.xxx
"""

from os import environ
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件（在项目根目录）
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class Settings:
    """全局配置，所有配置项集中在此。

    新增配置项时在此类中添加属性即可，统一管理。
    """

    # ── Yelp API ───────────────────────────────────────────
    YELP_API_KEY: str = environ.get("YELP_API", "")
    YELP_CLIENT_ID: str = environ.get("CLIENT_ID", "")
    YELP_API_BASE_URL: str = "https://api.yelp.com/v3"

    # ── 数据库 ─────────────────────────────────────────────
    DATABASE_URL: str = environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://tjll:tjll_dev@localhost:5432/tjll",
    )
    DATABASE_ECHO: bool = environ.get("DATABASE_ECHO", "").lower() == "true"

    # ── 服务器 ─────────────────────────────────────────────
    APP_HOST: str = environ.get("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(environ.get("APP_PORT", "8000"))


settings = Settings()
