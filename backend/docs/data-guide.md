# Yelp 学术数据集 — 数据加载与接口指南

> Yelp 公开学术数据集（JSONL 格式）的加载、存储与查询接口说明。

---

## 目录

- [数据集说明](#数据集说明)
- [快速开始](#快速开始)
- [两阶段加载流程](#两阶段加载流程)
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
| `yelp_academic_dataset_review.json` | ~5.3 GB | 7M | 用户评论 |
| `yelp_academic_dataset_user.json` | ~3.4 GB | 1.9M | 用户信息 |
| `yelp_academic_dataset_tip.json` | ~181 MB | 1.1M | 商家小贴士（暂未加载） |
| `yelp_academic_dataset_checkin.json` | ~287 MB | 130k | 签到记录（暂未加载） |

当前数据库表：**businesses**、**reviews**、**users**。

---

## 快速开始

### 前置条件

```bash
docker compose up -d          # 启动 PostgreSQL
```

### 加载数据

```bash
just data-load 50 10          # 最多 50 个商家，每个至少 10 条有效评论
# 等价于：
uv run python -m backend.scripts.extract_yelp_data --max-businesses 50 --min-reviews 10
```

脚本会自动：
1. 扫描已有 JSONL 文件（不存在则从 `data/Yelp-JSON.zip` 解压）
2. **第一阶段**：扫描三个 JSON 文件，按条件筛选出商家/评论/用户列表
3. **第二阶段**：批量写入 PostgreSQL

### 快速验证

```bash
just data-sample              # 等价于 just data-load 5 1
```

---

## 两阶段加载流程

```
第一阶段（扫描，不写 DB）
──────────────────────
yelp_academic_dataset_business.json
       ↓ 条件筛选（max_businesses, min_reviews）
商家候选列表
       ↓
yelp_academic_dataset_review.json
       ↓ 匹配商家 ID
评论候选列表 + 需要加载的用户 ID 集合
       ↓
yelp_academic_dataset_user.json
       ↓ 匹配用户 ID
用户候选列表
       ↓ 过滤
         - 去掉用户不存在的评论
         - 评论数不足 min_reviews 的商家丢弃
         - 被丢弃的商家不计入 max_businesses 计数
最终列表：商家 / 评论 / 用户

第二阶段（写入 DB）
──────────────────────
ConvertedBusiness  →  INSERT INTO businesses
ConvertedUser      →  INSERT INTO users
ConvertedReview    →  INSERT INTO reviews（校验外键）
```

### 过滤规则

- 商家 `review_count` ≥ `min_reviews` 才进入候选
- 只加载候选商家的评论
- 只加载候选评论涉及的用户
- **评论的用户不存在** → 丢弃该评论，且不计入该商家的有效评论数
- **商家有效评论数 < `min_reviews`** → 丢弃该商家（不计入 max_businesses）

---

## 加载脚本参考

### `backend/scripts/extract_yelp_data.py`

```bash
uv run python -m backend.scripts.extract_yelp_data \
    --max-businesses 100 \      # 最多加载的商家数
    --min-reviews 20 \          # 商家最低有效评论数
    --batch-size 500 \          # 每批写入行数
    --skip-load                 # 仅解压不加载
```

### `backend/data/loader.py`

```python
import asyncio
from backend.data.loader import load_all_yelp_data

stats = asyncio.run(load_all_yelp_data(
    max_businesses=50,
    min_reviews=10,
    batch_size=200,
))
print(stats["filtered"])   # {businesses: 50, reviews: 1234, users: 567}
print(stats["scan"])       # {biz_total: 150000, rev_total: ...}
```

也可单独调用两阶段：

```python
from backend.data.loader import scan_phase, load_phase

# 第一阶段：扫描（不写 DB）
scan = await scan_phase(max_businesses=50, min_reviews=10)

# 第二阶段：写入
result = await load_phase(**scan)
```

---

## 数据接口

### Python 数据接口（函数调用）

```python
from backend.data.service import DataService

svc = DataService()

# 商家
biz = await svc.get_business("some-id")
businesses, total = await svc.list_businesses(keyword="pizza", min_rating=4.0)

# 评论
reviews, total = await svc.get_reviews_by_business("some-id")
review = await svc.get_review("review-id")

# 统计
stats = await svc.get_stats()

# RAG 批量
ids = await svc.get_all_business_ids()
texts = await svc.get_reviews_texts_by_business("some-id")
```

接口说明见 `backend/data/service.py`。

---

## 常见问题

### Q: 如何检查数据已正确加载？

```bash
just data-check
```

### Q: 加载太慢怎么办？

两阶段加载只处理指定数量的商家及其关联数据，比全量加载快得多。

```bash
# 先小批量验证
just data-sample

# 再逐步增加
just data-load 200 20
```

### Q: `is_closed` 的含义？

学术数据集的 `is_open`（1=营业，0=关闭）→ ORM 中 `is_closed` 取反。
