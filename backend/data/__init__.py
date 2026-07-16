"""Data 子模块 —— Yelp 学术数据集加载与数据接口。

快速入门：
    # 加载数据
    uv run python backend/scripts/extract_yelp_data.py

    # 在代码中使用
    from backend.data.service import DataService
    svc = DataService()
    biz = await svc.get_business("some-id")

目录：
  - schemas.py: Yelp 学术数据集 JSONL 的 Pydantic 模型
  - loader.py:  将 JSONL 数据批量写入 PostgreSQL（兼容现有 ORM 表结构）
  - service.py: 为其他模块提供数据库查询接口（函数调用）
"""

from __future__ import annotations

from backend.data.loader import load_all_yelp_data, load_businesses, load_reviews
from backend.data.service import DataService

__all__ = [
    "DataService",
    "load_all_yelp_data",
    "load_businesses",
    "load_reviews",
]
