# TJLL 项目架构

> 大众点评 AI 智能助手 — 前后端分离项目架构文档

---

## 总体架构

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

## 后端模块划分

### 路由层 (`backend/routers/`)

| 模块 | 前缀 | 说明 |
|------|------|------|
| `health.py` | `/health` | 健康检查 |
| `auth.py` | `/api/auth` | 注册、登录、退出 |
| `user.py` | `/api/user` | 用户信息获取与更新 |
| `business.py` | `/api/business` | 商家列表、详情 |
| `review.py` | `/api/review` | 评论列表、详情 |
| `ai.py` | `/api/ai` | AI 对话、推荐、评论总结 |
| `favorite.py` | `/api/favorites` | 收藏增删查 |
| `admin.py` | `/api/admin` | 管理后台接口 |

### 业务逻辑层 (`backend/services/`)

| 模块 | 说明 |
|------|------|
| `auth.py` | 注册/登录/退出逻辑 |
| `user.py` | 用户信息 CRUD |
| `business.py` | 商家查询（DB + Yelp API） |
| `review.py` | 评论查询 |
| `ai.py` | AI 对话/推荐/总结 |
| `favorite.py` | 收藏管理 |
| `yelp.py` / `yelp_search.py` | Yelp 外部 API 调用 |

### 数据模型层 (`backend/models/`)

| 模型 | 表名 | 说明 |
|------|------|------|
| `Business` | `businesses` | Yelp 商家数据 |
| `Review` | `reviews` | Yelp 评论数据 |
| `User` (Yelp) | `users` | Yelp 用户（数据集） |
| `AppUser` | `app_users` | 平台应用用户 |
| `Favorite` | `favorites` | 用户收藏 |

### 数据流示意

```
Frontend → Router → Service → Model/ORM → PostgreSQL
                ↘           ↙
            Pydantic Schema (验证/序列化)
```

> 字段映射与 API 响应格式详见 [`docs/api-need.md`](api-need.md)。

---

## 认证架构

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

## RAG 架构（独立子系统）

```
Yelp Dataset → 数据清洗 → OpenSearch Index
                              ↓
用户 Query → LLM → 检索增强 → 排序重排 → 最终响应
```

> 详见 [`docs/guides/rag-llm.md`](guides/rag-llm.md)
