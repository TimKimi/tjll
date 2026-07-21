"""数据库配置 — PostgreSQL + Redis。"""

from __future__ import annotations


class DatabaseMixin:
    """数据库连接配置。

    所有默认值在此统一修改。
    """

    # ── PostgreSQL ───────────────────────────────────────────
    # 连接串格式：postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: str = "postgresql+asyncpg://tjll:tjll_dev@localhost:5432/tjll"
    # 是否打印 SQL 语句（开发调试用）
    DATABASE_ECHO: bool = False

    # ── Redis（对话历史缓存）──
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = "Jianyan_01"
    # 对话历史过期时间（秒），默认 24h
    redis_history_ttl: int = 86400

    # ── 派生属性 ─────────────────────────────────────────────

    @property
    def redis_url(self) -> str:
        """Redis 连接串。"""
        return (
            f"redis://:{self.redis_password}"
            f"@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        )
