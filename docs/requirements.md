# 项目需求文档

> 大众点评 AI 智能助手 — 项目需求总览

---

## 一、项目概述

基于 Yelp 学术数据集，构建一个大众点评风格的 AI 智能助手平台，提供商家浏览、评论查看、AI 智能推荐、收藏管理等功能，并支持管理后台。

---

## 二、功能需求

### P0 — 核心功能（必须有）

| 需求 | 说明 | 状态 |
|------|------|------|
| 商家列表/搜索 | 分页查询，支持关键词、分类、价格筛选 | ✅ 已有 |
| 商家详情 | 查看商家的完整信息 | ✅ 已有 |
| 评论列表 | 查看商家评论，支持排序 | ✅ 已有 |
| 用户注册/登录 | 用户名密码注册，JWT 认证 | ✅ 已实现 |
| AI 对话 | 智能问答，推荐商家 | ✅ 已有 |
| AI 推荐 | 基于条件推荐商家 | ✅ 已有 |
| AI 评论总结 | 自动总结商家口碑 | ✅ 已有 |
| AI 生成点评 | 辅助用户写评论 | ✅ 已有 |
| 健康检查 | 服务连通性验证 | ✅ 已有 |

### P1 — 重要功能

| 需求 | 说明 | 状态 |
|------|------|------|
| 用户信息管理 | 获取/更新个人信息 | ✅ 已实现 |
| 管理员登录 | 使用 admin 账号登录 | ✅ 已实现 |
| 收藏管理 | 收藏/取消收藏/列表 | ✅ 已实现 |
| 管理员信息 | 获取当前管理员信息 | 🟡 开发中 |
| 用户管理（Admin） | 管理员查看所有用户列表 | 🟡 开发中 |
| 对话管理 | 对话 CRUD | 📋 待开发 |
| 头像上传 | 用户头像上传 | 📋 待开发 |

### P2 — 增强功能

| 需求 | 说明 | 状态 |
|------|------|------|
| 评论接口改造 | POST → GET + 路径参数 | 📋 待开发 |
| AI Chat 推荐卡片 | 响应中增加 Shop 对象 | 📋 待开发 |
| OpenSearch 集成 | 向量检索增强 | ✅ 已有 |
| RAG 管道 | 检索增强生成 | ✅ 已有 |

---

## 三、非功能需求

| 需求 | 说明 |
|------|------|
| 性能 | 接口响应 < 500ms（不含 AI 调用） |
| 安全 | 密码 bcrypt 哈希，JWT 认证 |
| 可用性 | 服务健康检查，错误友好提示 |
| 可维护性 | Ruff 代码检查，mypy 类型检查，单元测试 |
| 可扩展性 | 模块化路由/服务/模型分层 |

---

## 四、开发分支规划

| 分支 | 内容 | 状态 |
|------|------|------|
| `feat/user-auth` | 认证 + 用户模块 | ✅ 已合并 |
| `feat/favorites` | 收藏模块 | ✅ 已合并 |
| `feat/admin` | 管理后台 | 🟡 开发中 |
| `feat/review-api` | 评论接口改造 | 📋 待开发 |
| `feat/conversation` | 对话管理 | 📋 待开发 |
| `feat/ai-response-shop` | AI 推荐卡片 | 📋 待开发 |
| `feat/avatar-upload` | 头像上传 | 📋 待开发 |

---

## 五、API 接口总览

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/health` | 健康检查 | ✅ |
| POST | `/api/auth/register` | 用户注册 | ✅ |
| POST | `/api/auth/login` | 用户登录 | ✅ |
| POST | `/api/auth/admin/login` | 管理员登录 | ✅ |
| POST | `/api/auth/logout` | 退出登录 | ✅ |
| GET | `/api/user/profile` | 获取用户信息 | ✅ |
| PUT | `/api/user/profile` | 更新用户信息 | ✅ |
| POST | `/api/business/list` | 商家列表 | ✅ |
| POST | `/api/business/{id}` | 商家详情 | ✅ |
| POST | `/api/review/list` | 评论列表 | ✅ |
| POST | `/api/review/{id}` | 评论详情 | ✅ |
| POST | `/api/ai/chat` | AI 对话 | ✅ |
| POST | `/api/ai/recommend` | AI 推荐 | ✅ |
| POST | `/api/ai/review-summary` | AI 评论总结 | ✅ |
| POST | `/api/ai/generate-review` | AI 生成点评 | ✅ |
| GET | `/api/favorites` | 收藏列表 | ✅ |
| POST | `/api/favorites` | 添加收藏 | ✅ |
| DELETE | `/api/favorites/{shop_id}` | 移除收藏 | ✅ |
| GET | `/api/admin/profile` | 管理员信息 | 🟡 |
| GET | `/api/admin/users` | 用户列表 | 🟡 |

> 完整 API 文档见 `docs/api-need.md`
