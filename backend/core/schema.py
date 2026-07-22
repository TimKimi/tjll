"""开发环境自动适配表结构。

检测 ORM 定义与数据库实际表结构差异，自动建表/加列，
避免每次改模型都需要手写 SQL 迁移。
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.models.base import Base

logger = logging.getLogger("backend.core.schema")


async def auto_adapt_schema(engine: AsyncEngine) -> None:
    """遍历 ORM 所有表，自动补齐缺失的表和列。

    仅新增，不删不改（数据安全优先）。
    server_default 由 ORM 层处理，DDL 中不追加默认值。
    """
    dialect = postgresql.dialect()
    stats = {"tables": 0, "created": 0, "columns_added": 0}

    async with engine.connect() as conn:
        for table_name, table in Base.metadata.tables.items():
            stats["tables"] += 1
            result = await conn.execute(
                text(
                    "SELECT EXISTS ("
                    "  SELECT FROM information_schema.tables"
                    "  WHERE table_name = :name"
                    ")"
                ),
                {"name": table_name},
            )
            table_exists = result.scalar()

            if not table_exists:
                logger.info("自动创建表: %s", table_name)
                await conn.run_sync(table.create)
                stats["created"] += 1
                continue

            logger.debug("检查表: %s (%d 列)", table_name, len(table.columns))
            for column in table.columns:
                result = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "  SELECT FROM information_schema.columns"
                        "  WHERE table_name = :table AND column_name = :col"
                        ")"
                    ),
                    {"table": table_name, "col": column.name},
                )
                col_exists = result.scalar()

                if col_exists:
                    continue

                type_str = column.type.compile(dialect=dialect)
                sql = (
                    f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {type_str}'
                )
                logger.info("自动新增列: %s.%s (%s)", table_name, column.name, type_str)
                try:
                    await conn.execute(text(sql))
                    stats["columns_added"] += 1
                except Exception:
                    logger.warning(
                        "新增列失败 %s.%s，可能已存在或类型不兼容",
                        table_name,
                        column.name,
                        exc_info=True,
                    )

        await conn.commit()

    logger.info(
        "schema 适配完成: 检查 %d 张表，新建 %d 张，新增 %d 列",
        stats["tables"],
        stats["created"],
        stats["columns_added"],
    )
