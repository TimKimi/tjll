# 架构决策记录 (ADR)

> 记录项目的关键技术决策及其上下文。

---

## ADR-001: 使用 FastAPI 作为后端框架

- **日期**: 2026-07-01
- **状态**: ✅ 已采纳

### 上下文
需要构建一个高性能的异步 API 服务，支持 AI 对话流式响应。

### 决策
选择 FastAPI 而非 Django REST Framework 或 Flask。

### 理由
- 原生异步支持，适合 LLM 流式响应
- 自动生成 OpenAPI 文档
- Pydantic 模型即 Schema，减少重复代码
- 性能接近 Node.js/Go

---

## ADR-002: 使用 uv 替代 pip 管理依赖

- **日期**: 2026-07-01
- **状态**: ✅ 已采纳

### 上下文
需要快速、可靠的 Python 包管理方案。

### 决策
使用 uv（Astral 出品）替代 pip/poetry。

### 理由
- 比 pip 快 10-100 倍
- 兼容 `pyproject.toml` 标准
- 自动锁定版本（`uv.lock`）

---

## ADR-003: Git Flow 简化版分支策略

- **日期**: 2026-07-01
- **状态**: ✅ 已采纳

### 上下文
多人协作需要统一的分支管理策略。

### 决策
采用 Git Flow 简化版：`master` / `develop` / `feat/*` / `fix/*` / `hotfix/*`。

### 理由
- 清晰区分开发/发布/修复场景
- 比纯 Git Flow 轻量，适合中小团队
- PR + Code Review 流程保障代码质量

---

## ADR-004: 统一的 `ApiResponse[T]` 响应格式

- **日期**: 2026-07-10
- **状态**: ✅ 已采纳

### 上下文
前后端需要统一的数据交换格式。

### 决策
使用泛型 `ApiResponse[T]`，`code: 0` 表示成功，非 0 表示错误。

### 理由
- 与前端约定 `code === 0` 判断成功
- 泛型支持不同 data 类型
- 分页使用 `PaginatedData[T]`

---

## ADR-005: 使用 UUID 短 ID（22 字符）替代自增主键

- **日期**: 2026-07-10
- **状态**: ✅ 已采纳

### 上下文
用户 ID 需要防枚举，且与 Yelp 的 22 字符 ID 风格一致。

### 决策
使用 `uuid.uuid4().hex[:22]` 生成 ID。

### 理由
- 防止用户 ID 枚举攻击
- 与 Yelp Business ID 风格一致
- 比自增 ID 更适合分布式场景

---

## ADR-006: 统一使用 `app_users` 表，通过 `role` 字段区分用户与管理员

- **日期**: 2026-07-15
- **状态**: ✅ 已采纳

### 上下文
需要支持普通用户和管理员两种角色，但不希望维护两张用户表。

### 决策
在 `AppUser` 模型中增加 `role` 字段（`user` / `admin`），通过 JWT 中间件校验权限。

### 理由
- 减少表数量，简化数据模型
- 管理员也是用户，共享基础信息
- 权限校验通过中间件统一处理

---

## ADR-007: 使用 snake_case 作为前后端 API 字段风格

- **日期**: 2026-07-15
- **状态**: ✅ 已采纳

### 上下文
Python 后端默认 snake_case，前端 JavaScript/TypeScript 使用 camelCase。

### 决策
后端统一使用 snake_case，前端在消费 API 时做映射转换。

### 理由
- 后端 Python 生态系统默认 snake_case
- FastAPI/Pydantic 原生支持 snake_case
- 前端可用工具自动转换（如 `camelcase-keys`）

---

## ADR-008: 收藏模块的 `shop_id` 指向 Business 表

- **日期**: 2026-07-18
- **状态**: ✅ 已采纳

### 上下文
需要确定收藏模块中 `shop_id` 的参照对象。

### 决策
`Favorite.shop_id` 作为外键关联 `Business.id`（Yelp 商家 ID）。

### 理由
- 收藏对象是商家（Business），无需独立 Shop 表
- 直接复用已有的 Yelp Business 数据
- 前端"推荐卡片"（Shop）和"餐厅"（Restaurant）均映射到 Business

---

## ADR-009: Admin 模块使用独立路由但复用 Auth 中间件

- **日期**: 2026-07-21
- **状态**: ✅ 已采纳

### 上下文
管理后台接口需要严格的权限控制。

### 决策
Admin 路由（`/api/admin/*`）复用 `get_current_user` 中间件，在 Service 层校验 `role == "admin"`。

### 理由
- 复用已有 JWT 认证体系
- 避免重复编写认证逻辑
- Service 层校验便于单元测试
