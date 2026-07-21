# 后端开发指南

> 环境搭建、架构说明与 Yelp 数据处理。

---

## 环境搭建

```bash
just install              # 安装依赖 + git 钩子
docker compose up -d      # 启动 PostgreSQL
just serve                # 启动开发服务器（热重载，自动建表）
```

浏览器打开 `http://127.0.0.1:8000/docs` 查看 Swagger UI。

---

## 三层架构

```
routers/  →  services/  →  models/  +  schemas/
 路由层       服务层        ORM 模型    Pydantic 模型
```

| 层 | 职责 | 依赖方向 |
|---|---|---|
| `routers/` | 定义 HTTP 端点、参数校验、异常处理 | → services |
| `services/` | 业务逻辑编排、数据库读写 | → schemas, models |
| `schemas/` | Pydantic 请求/响应模型（与 ORM 分离） | 无 |
| `models/` | SQLAlchemy 表映射 | → database |

### 新增一个模块

四步走：

1. **Schema** — `backend/schemas/{module}.py`，定义请求/响应模型
2. **Service** — `backend/services/{module}.py`，实现业务逻辑
3. **Router** — `backend/routers/{module}.py`，挂载 HTTP 端点
4. **注册** — `backend/main.py` 添加 `app.include_router(…)`

---

## 数据库

```bash
docker compose up -d       # 启动
docker compose down        # 停止
docker compose exec -T db psql -U tjll -d tjll   # 手动查询
```

应用启动时自动建表（`Base.metadata.create_all`），不会自动执行 `ALTER TABLE`，改表结构需手动执行 DDL。

---

## Yelp 数据处理

### 数据集

| 文件 | 大小 | 行数 | 说明 |
|---|---|---|---|
| `yelp_academic_dataset_business.json` | ~119 MB | 150k | 商家 |
| `yelp_academic_dataset_review.json` | ~5.3 GB | 7M | 评论 |
| `yelp_academic_dataset_user.json` | ~3.4 GB | 1.9M | 用户 |

### 加载数据

```bash
just dload 100 10    # 最多 100 商家，每商家 ≥10 条有效评论
just dsample          # 小批量（等价于 just dload 5 1）
just dstat            # 查看数据库统计
```

### 两阶段加载流程

```
第一阶段（扫描，不写 DB）
  商家 JSON → 按条件筛选 → 商家候选列表
  评论 JSON → 匹配商家 ID → 评论候选列表 + 用户 ID
  用户 JSON → 匹配用户 ID → 用户候选列表
          ↓ 过滤掉用户不存在 的评论 / 评论不足的商家

第二阶段（批量写入 DB）
  ConvertedBusiness → INSERT INTO businesses
  ConvertedUser     → INSERT INTO users
  ConvertedReview   → INSERT INTO reviews
```

### 字段映射

| 数据集字段 | ORM 字段 | 说明 |
|---|---|---|
| `business_id` | `id` | 22 字符主键 |
| `stars` | `rating` | review 整数，business 浮点数 |
| `is_open` (1/0) | `is_closed` (bool) | 取反 |
| `categories` (逗号字符串) | `categories` (JSON) | `[{alias, title}]` |
| `hours` (天→时段) | `business_hours` (JSON) | |
| 地址字段 | `address` (JSON) | 合并为 YelpLocation |
| `date` | `time_created` | 直接映射 |
| `user_id` | `user` (JSON) | 存为 `{"id": user_id}` |

### Python 数据接口

```python
from backend.data.service import DataService

svc = DataService()
biz = await svc.get_business("some-id")
results, total = await svc.list_businesses(keyword="pizza", min_rating=4.0)
reviews, total = await svc.get_reviews_by_business("some-id")
stats = await svc.get_stats()
```
