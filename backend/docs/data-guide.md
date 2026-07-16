# Yelp 学术数据集 — 数据加载与接口指南

> Yelp 公开学术数据集（JSONL 格式）的加载、存储与查询接口说明。

---

## 目录

- [数据集说明](#数据集说明)
- [快速开始](#快速开始)
- [数据加载流程](#数据加载流程)
- [字段映射](#字段映射)
- [数据接口](#数据接口)
- [加载脚本参考](#加载脚本参考)
- [常见问题](#常见问题)

---

## 数据集说明

本模块使用 [Yelp 公开数据集](https://www.yelp.com/dataset)（Academic Dataset），
包含以下 JSONL 文件：

| 文件 | 大小 | 行数（约） | 说明 |
|---|---|---|---|
| `yelp_academic_dataset_business.json` | ~119 MB | 150k | 商家信息 |
| `yelp_academic_dataset_review.json` | ~5.3 GB | 7M | 用户评论（主要数据集） |
| `yelp_academic_dataset_user.json` | ~3.4 GB | 1.9M | 用户信息 |
| `yelp_academic_dataset_tip.json` | ~181 MB | 1.1M | 商家小贴士 |
| `yelp_academic_dataset_checkin.json` | ~287 MB | 130k | 签到记录 |

> 目前系统已加载 **商家** 和 **评论** 两张表到 PostgreSQL。
> 用户、小贴士、签到数据待后续按需扩展。

---

## 快速开始

### 前置条件

1. Docker PostgreSQL 运行中：
   ```bash
   docker compose up -d
   ```

2. 数据压缩包存在 `data/Yelp-JSON.zip`

### 一键加载

```bash
uv run python backend/scripts/extract_yelp_data.py
```

### 测试加载（少量数据）

```bash
uv run python backend/scripts/extract_yelp_data.py --max-businesses 100 --max-reviews 500
```

### 仅解压，不加载

```bash
uv run python backend/scripts/extract_yelp_data.py --skip-load
```

---

## 数据加载流程

```
data/Yelp-JSON.zip
       ↓ 解压
yelp_dataset.tar
       ↓ 提取
yelp_academic_dataset_*.json  (JSONL 格式，每行一个 JSON)
       ↓ 流式读取
DatasetBusiness / DatasetReview  (Pydantic 模型)
       ↓ 字段映射
ConvertedBusiness / ConvertedReview  (ORM 兼容格式)
       ↓ 批量 INSERT
PostgreSQL (businesses / reviews 表)
```

### 加载特性

- **流式处理**：5.3GB 评论文件按 1MB 块读取，内存占用稳定
- **批量写入**：每 500 条一次 `commit`，平衡吞吐和事务大小
- **断点续传**：自动跳过已存在的 `id`（`PRIMARY KEY` 冲突检测）
- **错误隔离**：单行解析失败仅跳过该行，不影响整体流程
- **进度日志**：每秒输出处理进度

---

## 字段映射

### 商家字段映射

Yelp 学术数据集的字段命名和结构与 Yelp Fusion API 不同。
加载器会自动完成以下映射：

| 学术数据集字段 | ORM 字段 | 转换说明 |
|---|---|---|
| `business_id` | `id` | 直接映射（22 字符主键） |
| `name` | `name` | 直接映射 |
| — | `alias` | 从 `name` 自动生成小写连字符形式 |
| `stars` | `rating` | 浮点数评分映射 |
| `review_count` | `review_count` | 直接映射 |
| `is_open` (1/0) | `is_closed` | `is_open == 0` 时 `is_closed = True` |
| `categories` (逗号分隔) | `categories` | 转为 `[{"alias": "...", "title": "..."}]` JSON |
| `address` + `city` + `state` + `postal_code` | `address` | 合并为 `YelpLocation` 格式 JSON |
| `latitude` / `longitude` | `latitude` / `longitude` | 直接映射 |
| `hours` (day-based) | `business_hours` | 转为 Yelp API 格式 JSON |
| `attributes` | — | 暂不存储 |

### 评论字段映射

| 学术数据集字段 | ORM 字段 | 转换说明 |
|---|---|---|
| `review_id` | `id` | 直接映射 |
| `business_id` | `business_id` | 外键关联 `businesses.id` |
| `stars` | `rating` | 整数评分 |
| `text` | `text` | 直接映射 |
| `date` | `time_created` | 直接映射 |
| `user_id` | `user` | 转为 `{"id": "user_id"}` JSON |
| `useful` / `funny` / `cool` | — | 暂不存储 |

### 营业时间转换

学术数据集使用天名称键（`"Monday": "8:0-18:30"`），
加载器将其转为 Yelp Fusion API 格式：

```json
{
  "open": [
    {"is_overnight": false, "start": "0800", "end": "1830", "day": 1}
  ],
  "hours_type": "REGULAR",
  "is_open_now": false
}
```

天数映射：`Monday=1, Tuesday=2, ..., Sunday=0`（与 Yelp API 一致）。

### 分类转换

学术数据集使用逗号分隔字符串，加载器将其转为结构化 JSON：

```
输入: "Doctors, Traditional Chinese Medicine, Acupuncture"
输出: [
  {"alias": "doctors", "title": "Doctors"},
  {"alias": "traditional-chinese-medicine", "title": "Traditional Chinese Medicine"},
  {"alias": "acupuncture", "title": "Acupuncture"}
]
```

---

## 数据接口

### Python 数据接口（函数调用）

`backend.data.service.DataService` 是其他模块访问 Yelp 数据库数据的统一入口。
直接在代码中 import 使用，无需经过 HTTP。

```python
from backend.data.service import DataService

svc = DataService()

# 获取商家详情
biz = await svc.get_business("some-id")

# 搜索商家
businesses, total = await svc.list_businesses(
    keyword="pizza",
    min_rating=4.0,
    sort_by="rating",
)

# 获取评论
reviews, total = await svc.get_reviews_by_business("some-id")

# 获取统计
stats = await svc.get_stats()

# 供 RAG 使用的批量接口
all_ids = await svc.get_all_business_ids()
texts = await svc.get_reviews_texts_by_business("some-id")
```

接口说明：

| 方法 | 返回 | 说明 |
|---|---|---|
| `get_business(business_id)` | `Business \| None` | 按 ID 获取商家 |
| `list_businesses(keyword, min_rating, category, sort_by, skip, limit)` | `(list[Business], int)` | 搜索/列出商家，支持过滤排序分页 |
| `get_business_with_reviews(business_id)` | `dict \| None` | 商家详情 + 所有评论 |
| `get_reviews_by_business(business_id, skip, limit)` | `(list[Review], int)` | 某商家的评论列表 |
| `get_review(review_id)` | `Review \| None` | 单条评论 |
| `get_stats()` | `dict` | 数据库统计 |
| `get_all_business_ids()` | `list[str]` | 所有商家 ID（供 RAG 批量处理） |
| `get_reviews_texts_by_business(business_id, limit)` | `list[str]` | 评论文本列表（供 RAG 检索） |

---

## 加载脚本参考

### `backend/scripts/extract_yelp_data.py`

```
用法:
  uv run python backend/scripts/extract_yelp_data.py

选项:
  --max-businesses N    限制商家数（默认全部）
  --max-reviews N       限制评论数（默认全部）
  --batch-size N        每批写入行数（默认 500）
  --skip-extract        跳过解压
  --skip-load           仅解压不加载
```

### `backend/data/loader.py`

模块化加载器，也可在其他脚本中直接调用：

```python
import asyncio
from backend.data.loader import load_all_yelp_data

stats = asyncio.run(load_all_yelp_data(
    max_businesses=1000,
    max_reviews=5000,
    batch_size=200,
))
print(stats)
```

---

## 常见问题

### Q: 如何检查数据已正确加载？

使用检查脚本：

```bash
uv run python backend/tests/scripts/check_db.py
```

### Q: 数据量太大，加载太慢怎么办？

建议：
1. 先用 `--max-businesses 1000 --max-reviews 5000` 测试
2. 全量加载评论（5.3GB）预计需要 20~60 分钟，取决于机器性能
3. 加载器支持断点续传，可以中断后重跑

### Q: 业务数据 `is_closed` 的含义？

学术数据集的 `is_open` 字段：`1`=营业中，`0`=已关闭。
ORM 中的 `is_closed` 是其取反：`is_open == 0 → is_closed = True`。

### Q: 为什么有些 JSON 字段存为字符串？

本项目的 ORM 模型将 `categories`、`address`、`hours` 等复杂结构存为
`TEXT` 类型的 JSON 字符串，与原有 Yelp Fusion API 数据的存储方式一致。
使用时通过 `json.loads()` 解析为 Python 对象。
