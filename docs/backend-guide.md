# TJLL 后端开发指南

> 基于 FastAPI 的团队协作规范

---

## 目录

- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [快速启动](#快速启动)
- [三层架构说明](#三层架构说明)
- [如何新增一个模块](#如何新增一个模块)
- [团队协作规范](#团队协作规范)
- [代码检查](#代码检查)
- [常见问题](#常见问题)

---

## 项目结构

```
backend/
├── __init__.py              # 包标识
├── main.py                  # FastAPI 应用入口，注册路由、挂载中间件
├── config.py                # 全局配置（环境变量 → Settings 对象）
├── routers/                 # 路由层 —— 定义 API 端点
│   ├── __init__.py
│   └── ...                  # 按业务模块拆分文件
├── services/                # 服务层 —— 业务逻辑 & 外部 API 调用
│   ├── __init__.py
│   └── ...                  # 一个模块一个文件
└── schemas/                 # 模型层 —— Pydantic 请求/响应模型
    ├── __init__.py
    └── ...                  # 一个模块一个文件
```

### 各层职责

| 层 | 目录 | 职责 | 依赖方向 |
|---|---|---|---|
| **路由层** | `routers/` | 定义 HTTP 端点、参数校验、状态码、异常处理 | → services |
| **服务层** | `services/` | 业务逻辑编排、外部 API 调用、数据处理 | → schemas |
| **模型层** | `schemas/` | Pydantic 模型（请求参数、响应体） | 无（纯数据类） |

**依赖规则：** `routers → services → schemas`，禁止逆向依赖。

---

## 技术栈

| 组件 | 技术 | 说明 |
|---|---|---|
| Web 框架 | FastAPI | 异步、自动生成 OpenAPI 文档 |
| HTTP 客户端 | httpx | 异步、与 FastAPI 原生配合 |
| 数据模型 | Pydantic | 内置 FastAPI，做请求/响应校验 |
| 包管理 | uv | 通过 `just add` 添加依赖 |
| 运行 | uvicorn | ASGI 服务器 |

---

## 快速启动

```bash
# 1. 安装所有依赖
just install

# 2. 启动开发服务器（热重载）
just serve

# 3. 浏览器打开
# http://127.0.0.1:8000/health   — 健康检查
# http://127.0.0.1:8000/docs     — Swagger UI
```

---

## 三层架构说明

### 1. Schemas（模型层）

定义请求参数和响应体的 Pydantic 模型，**不包含任何业务逻辑**。

**示例** `schemas/user.py`：

```python
from __future__ import annotations
from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
```

### 2. Services（服务层）

封装业务逻辑和外部 API 调用，**不直接处理 HTTP 请求**。

**示例** `services/user.py`：

```python
from __future__ import annotations
from backend.schemas.user import UserResponse


class UserService:
    """用户相关的业务逻辑。"""

    async def get_user(self, user_id: str) -> UserResponse:
        ...  # 调用数据库或外部 API
```

### 3. Routers（路由层）

暴露 HTTP 端点，只做参数校验 + 调用 Service，**不包含业务逻辑**。

**示例** `routers/user.py`：

```python
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from backend.schemas.user import UserResponse
from backend.services.user import UserService

router = APIRouter(prefix="/api/users", tags=["users"])
_service = UserService()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str) -> UserResponse:
    try:
        return await _service.get_user(user_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
```

### 4. 注册到 `main.py`

```python
from backend.routers import user  # ← 新增

app.include_router(user.router)    # ← 注册
```

---

## 如何新增一个模块

假设要新增一个 `review`（评论）模块，分四步走。

### 第一步：创建 Schema

```bash
touch backend/schemas/review.py
```

定义请求/响应模型：

```python
from __future__ import annotations
from pydantic import BaseModel


class ReviewOut(BaseModel):
    id: str
    content: str
    rating: int
```

### 第二步：创建 Service

```bash
touch backend/services/review.py
```

```python
from __future__ import annotations
from backend.schemas.review import ReviewOut


class ReviewService:
    async def list_reviews(self, business_id: str) -> list[ReviewOut]:
        ...
```

### 第三步：创建 Router

```bash
touch backend/routers/review.py
```

```python
from __future__ import annotations
from fastapi import APIRouter
from backend.schemas.review import ReviewOut
from backend.services.review import ReviewService

router = APIRouter(prefix="/api/reviews", tags=["reviews"])
_service = ReviewService()


@router.get("/{business_id}", response_model=list[ReviewOut])
async def list_reviews(business_id: str) -> list[ReviewOut]:
    return await _service.list_reviews(business_id)
```

### 第四步：注册到 `main.py`

```python
from backend.routers import review

app.include_router(review.router)
```

---

## 团队协作规范

### 1. 每人负责自己的模块

模块按文件级别拆分，一个人负责一个或多个文件，**不同人不同文件**，天然避免冲突。

| 团队成员 | 负责模块 | 涉及文件 |
|---|---|---|
| 成员 A | Yelp 商家搜索 | `routers/yelp.py` `services/yelp.py` `schemas/yelp.py` |
| 成员 B | 评论数据 | `routers/review.py` `services/review.py` `schemas/review.py` |
| 成员 C | 用户认证 | `routers/auth.py` `services/auth.py` `schemas/auth.py` |

> **规则：** 同一时刻只有一个人在自己的模块文件上工作。需要修改别人的文件时，先在群里说一声。

### 2. Git 分支策略

```
feat/yelp-search      ← 成员 A 的 Yelp 搜索模块
feat/review            ← 成员 B 的评论模块
feat/auth              ← 成员 C 的认证模块
```

- 从 `develop` 拉出功能分支
- **只在自己的分支上改自己的文件**
- 完成 → PR → Code Review → 合并到 `develop`

### 3. 谁修改 `main.py`？

`main.py` 是**共享文件**，谁加新模块谁就往里 `include_router`。

**避免冲突的技巧：**

- 把 `include_router` 放在**文件末尾的独立区域**
- 每人只加一行自己的 `app.include_router(...)`
- 如果和别人的修改冲突了，Git 合并很轻松（就是加一行）

```python
# ── 注册路由 ──────────────────────────────────────────────
app.include_router(yelp.router)    # A 负责
app.include_router(review.router)  # B 负责
app.include_router(auth.router)    # C 负责
```

### 4. 谁修改 `config.py`？

和 `main.py` 同理，在 `Settings` 类中新增自己的属性即可，每个人只加自己的配置项。

```python
class Settings:
    # ── 服务器 ─────────────────────────────────────────
    APP_HOST: str = ...
    APP_PORT: int = ...

    # ── A 的配置 ───────────────────────────────────────
    YELP_API_KEY: str = ...

    # ── B 的配置 ───────────────────────────────────────
    DATABASE_URL: str = ...
```

---

## 代码检查

```bash
# 提交前跑全套检查
just lint

# 单独运行
just fmt        # 格式化
just mypy       # 类型检查
```

---

## 常见问题

### `uvicorn` 找不到？

`fastapi` 的依赖没有直接包含 `uvicorn`，需要单独安装：

```bash
just add uvicorn
```

### 如何查看已安装的依赖？

```bash
uv tree          # 查看依赖树
uv sync          # 同步到 lock 文件版本
```

### Swagger 文档打不开？

确保服务器运行中，浏览器访问 `http://127.0.0.1:8000/docs`。

---

## 完整目录结构预览（未来）

```
backend/
├── __init__.py
├── main.py
├── config.py
├── routers/
│   ├── __init__.py
│   ├── yelp.py        ← Yelp 商家搜索
│   ├── review.py      ← 评论数据
│   └── ...            ← 后续模块依次添加
├── services/
│   ├── __init__.py
│   ├── yelp.py
│   ├── review.py
│   └── ...
└── schemas/
    ├── __init__.py
    ├── yelp.py
    ├── review.py
    └── ...
```

> **原则：** 一个文件就是一个独立的工作单元，不同人不同文件，互不干扰。
