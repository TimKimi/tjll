# TJLL 项目架构

> 大众点评 AI 智能助手 — 前后端分离项目架构文档

---

## 一、总体架构

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │ ──→ │  Backend API  │ ──→ │  PostgreSQL   │
│    (TBD)     │ ←── │  (FastAPI)    │ ←── │  (AsyncPG)    │
└─────────────┘      └──────┬───────┘      └──────────────┘
                            │
                    ┌───────┴───────┐
                    │  RAG / LLM    │
                    │  (LangChain)  │
                    └───────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| **后端框架** | FastAPI 0.139 | Python 异步 Web 框架 |
| **ORM** | SQLAlchemy 2.0+ | 异步 ORM，支持 asyncpg |
| **数据库** | PostgreSQL | 主数据存储 |
| **向量检索** | OpenSearch | 混合检索（BM25 + 向量） |
| **LLM** | DeepSeek V4 Flash | 智能对话与推荐 |
| **Embedding** | BGE-base-zh-v1.5 | 中文向量模型 |
| **Rerank** | BGE-reranker-v2-m3 | 精排模型 |
| **缓存** | Redis | 对话历史缓存 |
| **认证** | JWT (python-jose) + bcrypt | 用户认证 |
| **前端** | 待定 (TBD) | 前端框架 |

---

## 二、后端模块划分

### 2.1 路由层 (`backend/routers/`)

| 模块 | 前缀 | 说明 | 状态 |
|------|------|------|------|
| `health.py` | `/health` | 健康检查 | ✅ 已有 |
| `auth.py` | `/api/auth` | 注册、登录、退出 | ✅ 已实现 |
| `user.py` | `/api/user` | 用户信息获取与更新 | ✅ 已实现 |
| `business.py` | `/api/business` | 商家列表、详情 | ✅ 已有 |
| `review.py` | `/api/review` | 评论列表、详情 | ✅ 已有 |
| `ai.py` | `/api/ai` | AI 对话、推荐、评论总结 | ✅ 已有 |
| `favorite.py` | `/api/favorites` | 收藏增删查 | ✅ 已实现 |
| `admin.py` | `/api/admin` | 管理后台接口 | 🟡 开发中 |

### 2.2 业务逻辑层 (`backend/services/`)

| 模块 | 说明 | 状态 |
|------|------|------|
| `auth.py` | 注册/登录/退出逻辑 | ✅ |
| `user.py` | 用户信息 CRUD | ✅ |
| `business.py` | 商家查询（DB + Yelp API） | ✅ |
| `review.py` | 评论查询 | ✅ |
| `ai.py` | AI 对话/推荐/总结 | ✅ |
| `favorite.py` | 收藏管理 | ✅ |
| `yelp.py` / `yelp_search.py` | Yelp 外部 API 调用 | ✅ |

### 2.3 数据模型层 (`backend/models/`)

| 模型 | 表名 | 说明 |
|------|------|------|
| `Business` | `businesses` | Yelp 商家数据 |
| `Review` | `reviews` | Yelp 评论数据 |
| `User` (Yelp) | `users` | Yelp 用户（数据集） |
| `AppUser` | `app_users` | 平台应用用户 |
| `Favorite` | `favorites` | 用户收藏 |
| `Conversation` | `conversations` | 对话（待创建） |
| `Message` | `messages` | 消息（待创建） |

### 2.4 数据流示意

```
Frontend → Router → Service → Model/ORM → PostgreSQL
                ↘           ↙
            Pydantic Schema (验证/序列化)
```

---

## 三、前后端数据对齐

### 3.1 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 3.2 分页响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 10,
    "total_pages": 10
  }
}
```

### 3.3 字段映射

| 前端字段 | 后端字段 | 说明 |
|---------|---------|------|
| `name` | `username` | 用户名 |
| `isOnline` | `is_online` | 在线状态 |
| `image` | `image_url` | 封面图/头像 |
| `images` | `photos` | 图片列表 |
| `lat/lng` | `latitude/longitude` | 坐标 |
| `shopId` | `shop_id` | 商家 ID |

---

## 四、认证架构

```
用户 → 注册/登录 → JWT 签发 → 后续请求携带 Bearer Token
                                          ↓
                              Dependencies.get_current_user()
                                          ↓
                                 从 JWT 解析用户 ID
                                          ↓
                                  业务逻辑执行
```

- 密码使用 `bcrypt` 哈希存储
- JWT 默认 24 小时过期
- 用户角色：`user` / `admin`（通过 `role` 字段区分）

---

## 五、RAG 架构（独立子系统）

```
Yelp Dataset → 数据清洗 → OpenSearch Index
                              ↓
用户 Query → LLM → 检索增强 → 排序重排 → 最终响应
```

> 详见 `backend/docs/rag-llm-backend-guide.md`
