# 探店助手 - API 接口需求文档

> **版本**: v0.2
> **对齐说明**: 本文档基于前端需求，以后端（FastAPI + SQLAlchemy）的现有数据模型和接口风格为准重新整理。
> **响应格式**: 使用后端统一的 `ApiResponse[T]` 结构（`code: 0` 表示成功），分页使用 `PaginatedData[T]`。
> **ID 类型**: 所有 business_id / review_id 均为字符串（Yelp 22 字符 ID），非自增整数。

---

## 目录

- [一、通用约定](#一通用约定)
- [二、开发分支规划](#二开发分支规划)
- [三、认证模块（Auth）—— 待开发](#三认证模块auth待开发)
- [四、用户模块（User）—— 待开发](#四用户模块user待开发)
- [五、商家模块（Business）—— 已有 + 增强](#五商家模块business已有--增强)
- [六、评论模块（Review）—— 已有 + 改造](#六评论模块review已有--改造)
- [七、对话模块（Conversation）—— 待开发](#七对话模块conversation待开发)
- [八、AI 模块（AI）—— 已有 + 增强](#八ai模块ai已有--增强)
- [九、收藏模块（Favorite）—— 待开发](#九收藏模块favorite待开发)
- [十、管理后台模块（Admin）—— 待开发](#十管理后台模块admin待开发)
- [十一、健康检查（Health）—— 已有](#十一健康检查health已有)
- [十二、数据模型对齐](#十二数据模型对齐)
- [十三、错误码汇总](#十三错误码汇总)

---

## 一、通用约定

### 1.1 基础 URL

```
开发环境: http://localhost:8000
生产环境: https://api.example.com
```

> **注意**: 后端端口为 `8000`（uvicorn 默认），非前端文档中的 `3000`。前端开发代理需配置为 `8000`。

### 1.2 统一响应格式

后端使用泛型响应模型 `ApiResponse[T]`：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

| 字段    | 类型   | 说明                    |
|---------|--------|------------------------|
| code    | int    | 0 成功，非 0 表示错误   |
| message | string | 提示信息                |
| data    | T/null | 响应数据，失败时为 null |

> **与前端文档差异**: 后端成功 `code=0`，前端原文要求 `code=200`。
> **建议**: 前端按 `code === 0` 判断成功；如坚持 `code=200` 需在 `ApiResponse` 层做映射。

### 1.3 分页响应格式

后端使用 `PaginatedData[T]` 模型：

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

| 字段        | 类型 | 说明                  |
|-------------|------|-----------------------|
| items       | list | 当前页数据列表        |
| total       | int  | 总记录数              |
| page        | int  | 当前页码（从 1 开始） |
| page_size   | int  | 每页条数              |
| total_pages | int  | 总页数                |

> **与前端文档差异**: 前端使用 `limit` 做分页参数，后端使用 `page_size`。前端传参时需统一使用 `page_size`。

### 1.4 通用请求头

```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer {token}"
}
```

---

## 二、开发分支规划

按照项目 [Git Flow 简化版](../README.md#分支策略git-flow-简化版) 的分支策略，将 API 开发划分为以下独立分支：

| # | 分支名 | 内容 | 依赖 | 工作量 |
|---|--------|------|------|--------|
| 1 | `feat/user-auth` | 认证模块（注册/登录/退出）+ 用户模块（信息/头像上传） | 无（新建表） | 🔴🔴🔴 |
| 2 | `feat/conversation` | 对话 CRUD + 消息管理 + 对接 AI Chat | `feat/user-auth` | 🔴🔴 |
| 3 | `feat/favorites` | 收藏模块（增/删/查） | `feat/user-auth` | 🟢 已完成 |
| 4 | `feat/admin` | 管理员登录 + 用户管理列表 | `feat/user-auth` | 🟡 |
| 5 | `feat/review-api` | 评论路由改造：改 POST 为 GET + 路径参数 | 无 | 🟡 |
| 6 | `feat/ai-response-shop` | AI Chat 响应增加推荐卡片 Shop 对象 | `feat/conversation` | 🔴 |
| 7 | `feat/avatar-upload` | 头像上传接口（文件存储 + URL 回显） | `feat/user-auth` | 🟡 |

**建议开发顺序**: `1 → 2 → 3 → 4`（可并行 `5、7`）→ `6`

---

## 三、认证模块（Auth）—— 待开发

> **分支**: `feat/user-auth`
> **说明**: 后端目前无认证体系，需新增 `users` 表（应用用户）、JWT 签发与验证中间件、密码哈希（bcrypt）。

### 3.1 用户注册

```
POST /api/auth/register
```

**请求体**:

| 字段     | 类型   | 必填 | 说明                    |
|----------|--------|------|------------------------|
| username | string | ✅   | 用户名，2-16 位         |
| password | string | ✅   | 密码，至少 8 位         |
| email    | string | ❌   | 邮箱                    |

**成功响应** `201`:

```json
{
  "code": 0,
  "message": "注册成功",
  "data": {
    "id": "u_abc123",
    "username": "张三",
    "avatar": "",
    "register_time": "2026-07-19T14:30:00"
  }
}
```

**错误响应**:

| code | message              |
|------|----------------------|
| 400  | 用户名已存在          |
| 400  | 用户名格式错误        |
| 400  | 密码长度至少为 8 位   |

> **字段说明**: `id` 使用字符串而非整数（防枚举），`register_time` 使用 ISO8601 格式。

---

### 3.2 用户登录

```
POST /api/auth/login
```

**请求体**:

| 字段     | 类型    | 必填 | 说明           |
|----------|---------|------|---------------|
| username | string  | ✅   | 用户名           |
| password | string  | ✅   | 密码           |
| remember | boolean | ❌   | 是否记住我     |

**成功响应** `200`:

```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": "u_abc123",
      "username": "张三",
      "avatar": "",
      "is_online": true,
      "email": "",
      "bio": "",
      "register_time": "2026-07-19T14:30:00",
      "role": "user"
    }
  }
}
```

**错误响应**:

| code | message                  |
|------|--------------------------|
| 401  | 用户名或密码错误          |
| 404  | 用户不存在                |

> **字段差异**: `username` 而非前端文档的 `name`，`is_online` 而非 `isOnline`，遵循后端 `snake_case` 风格。

---

### 3.3 管理员登录

```
POST /api/auth/admin/login
```

**请求体**: 同用户登录。

**成功响应** `200`:

```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": "u_admin",
      "username": "管理员",
      "avatar": "https://example.com/admin_avatar.jpg",
      "is_online": true,
      "email": "admin@example.com",
      "bio": "平台管理员",
      "register_time": "2026-01-01T00:00:00",
      "role": "admin"
    }
  }
}
```

> **实现建议**: 统一使用 `users` 表，通过 `role` 字段（`user` / `admin`）区分，无需独立的管理员表。

---

### 3.4 退出登录

```
POST /api/auth/logout
```

**请求头**: `Authorization: Bearer {token}`

**成功响应** `200`:

```json
{
  "code": 0,
  "message": "退出成功",
  "data": null
}
```

> **实现建议**: 可配合 Redis 维护 token 黑名单，或简单返回成功由前端清除 token。

---

## 四、用户模块（User）—— 待开发

> **分支**: `feat/user-auth`
> **说明**: 依赖认证模块的 JWT 中间件。

### 4.1 获取用户信息

```
GET /api/user/profile
```

**请求头**: `Authorization: Bearer {token}`

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "id": "u_abc123",
    "username": "张三",
    "avatar": "",
    "is_online": true,
    "email": "",
    "bio": "",
    "register_time": "2026-07-19T14:30:00"
  }
}
```

**错误响应**:

| code | message              |
|------|----------------------|
| 401  | 未授权，请先登录      |

---

### 4.2 更新用户信息

```
PUT /api/user/profile
```

**请求头**: `Authorization: Bearer {token}`

**请求体**（全部选填）:

| 字段     | 类型   | 说明     |
|----------|--------|---------|
| username | string | 用户名   |
| email    | string | 邮箱     |
| bio      | string | 个性签名 |

**成功响应** `200`: 返回完整用户对象（同 4.1）。

---

### 4.3 上传头像

```
POST /api/user/avatar
```

**请求头**: `Authorization: Bearer {token}`
**Content-Type**: `multipart/form-data`

**请求体**:

| 字段   | 类型 | 必填 | 说明                          |
|--------|------|------|-------------------------------|
| avatar | File | ✅   | 图片文件（jpg/png/gif, ≤2MB） |

**成功响应** `200`:

```json
{
  "code": 0,
  "message": "上传成功",
  "data": {
    "avatar": "https://example.com/uploads/avatars/u_abc123.jpg"
  }
}
```

**错误响应**:

| code | message                        |
|------|--------------------------------|
| 400  | 文件格式不支持                  |
| 400  | 文件大小超过限制（最大 2MB）    |

> **实现建议**: 开发环境存 `backend/static/avatars/`，生产环境使用对象存储（OSS/S3）。

---

## 五、商家模块（Business）—— 已有 + 增强

> **分支**: 无需新建分支，已有实现（`backend/routers/business.py`）
> **说明**: 后端使用 Business 模型，数据来自 Yelp 学术数据集。
> **前端映射**: 前端文档中的"餐厅"（Restaurant）和"推荐卡片"（Shop）均对应后端 Business 模型。

### 5.1 商家列表（已有）

```
GET /api/business/list
```

**查询参数**:

| 字段      | 类型   | 必填 | 默认值   | 说明                                      |
|-----------|--------|------|---------|------------------------------------------|
| keyword   | string | ❌   | —       | 搜索关键词（按名称模糊匹配）              |
| category  | string | ❌   | —       | 分类别名（如 `chinese`, `hotpot`）        |
| location  | string | ❌   | —       | 城市/地区（如 `成都`）                    |
| price     | string | ❌   | —       | 价格区间，逗号分隔（如 `1,2,3`）          |
| sort_by   | string | ❌   | `rating` | 排序：`rating` / `review_count` / `distance` |
| page      | int    | ❌   | 1       | 页码                                     |
| page_size | int    | ❌   | 10      | 每页条数（最大 50）                      |
| source    | string | ❌   | `db`    | 数据来源：`db`（数据库）/ `yelp`（实时 API） |
| latitude  | float  | ❌   | —       | 纬度（配合 `source=yelp` 使用）           |
| longitude | float  | ❌   | —       | 经度（配合 `source=yelp` 使用）           |

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "biz_001",
        "alias": "test_biz",
        "name": "蜀九香火锅",
        "image_url": "https://example.com/shop1.jpg",
        "is_closed": false,
        "url": "https://yelp.com/biz/...",
        "review_count": 326,
        "rating": 4.8,
        "price": "$$",
        "categories": [
          { "alias": "hotpot", "title": "火锅" }
        ],
        "location": {
          "address1": "春熙路88号",
          "city": "成都",
          "state": "SC",
          "zip_code": "610000",
          "country": "CN",
          "display_address": ["春熙路88号"]
        },
        "coordinates": {
          "latitude": 30.6595,
          "longitude": 104.0786
        },
        "display_phone": "+86 28 88888888",
        "transactions": ["delivery"],
        "photos": ["https://example.com/photo.jpg"],
        "hours": null
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10,
    "total_pages": 1
  }
}
```

> **与前端差异**:
> - 前端使用 `image`，后端为 `image_url`
> - 前端 `price` 为整数（人均价），后端为字符串（`$` / `$$` / `$$$`）
> - 前端用 `lat` / `lng`，后端用 `latitude` / `longitude`
> - 后端返回完整 `BusinessDetail`，含 `alias`、`is_closed`、`url`、`transactions`、`photos`、`hours` 等前端未列字段，前端按需取用

---

### 5.2 商家详情（已有）

```
GET /api/business/{business_id}
```

**路径参数**:

| 字段        | 类型   | 说明                         |
|-------------|--------|------------------------------|
| business_id | string | Yelp 商家 ID（22 字符字符串） |

**成功响应** `200`: 返回完整的 `BusinessDetail` 对象（结构同 5.1 的 items 内单个对象）。

**错误响应**:

| code | message      |
|------|-------------|
| 404  | 店铺不存在    |

> **前端新增需求映射**: 详情中的 `photos` 对应前端 `images` 数组，可用于图片轮播。

---

## 六、评论模块（Review）—— 已有 + 改造

> **分支**: `feat/review-api`
> **说明**: 后端已有评论接口，但使用 POST 方法。建议按 RESTful 规范改造为 GET + 路径参数，以匹配前端 `GET /api/restaurants/{id}/reviews` 的设计。

### 6.1 商家评论列表（改造建议）

**当前实现（POST，不建议前端直接调用）**:

```
POST /api/review/list?business_id=xxx&page=1&page_size=10
```

**建议改造为（GET + 路径参数）**:

```
GET /api/business/{business_id}/reviews
```

**查询参数**:

| 字段      | 类型   | 必填 | 默认值     | 说明                                      |
|-----------|--------|------|-----------|------------------------------------------|
| page      | int    | ❌   | 1         | 页码                                      |
| page_size | int    | ❌   | 10        | 每页条数（最大 50）                       |
| sort_by   | string | ❌   | `time`    | 排序：`time` / `rating_high` / `rating_low` |
| source    | string | ❌   | `db`      | 数据来源：`db` / `yelp`                   |

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "rev_001",
        "business_id": "biz_001",
        "text": "味道太棒了！强烈推荐！",
        "rating": 5,
        "time_created": "2026-07-15",
        "user": {
          "id": "user_001",
          "name": "美食达人小王",
          "profile_url": "https://example.com/u1",
          "image_url": "https://example.com/avatar1.jpg"
        },
        "url": "https://yelp.com/review/rev_001"
      }
    ],
    "total": 326,
    "page": 1,
    "page_size": 10,
    "total_pages": 33
  }
}
```

**错误响应**:

| code | message      |
|------|-------------|
| 404  | 商家不存在    |

---

### 6.2 评论详情（已有，无需改动）

```
POST /api/review/{review_id}
```

> **说明**: 此接口保持原有 POST 方法不变，前端通常无需直接调用，仅内部调试使用。

---

## 七、对话模块（Conversation）—— 待开发

> **分支**: `feat/conversation`
> **说明**: 后端尚无论对话管理，需新增 `conversations` 表和 `messages` 表，支持对话 CRUD 与 AI 对话集成。

### 7.1 获取对话列表

```
GET /api/conversations
```

**请求头**: `Authorization: Bearer {token}`

**查询参数**:

| 字段      | 类型 | 必填 | 默认值 | 说明     |
|-----------|------|------|--------|---------|
| page      | int  | ❌   | 1      | 页码     |
| page_size | int  | ❌   | 20     | 每页条数 |

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "conv_001",
        "title": "推荐附近好吃的川菜",
        "updated_at": "2026-07-19T14:30:00",
        "message_count": 5,
        "icon": "fas fa-comment"
      }
    ],
    "total": 2,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

---

### 7.2 获取对话消息

```
GET /api/conversations/{conversation_id}
```

**请求头**: `Authorization: Bearer {token}`

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "id": "conv_001",
    "title": "推荐附近好吃的川菜",
    "messages": [
      {
        "id": "msg_001",
        "role": "user",
        "content": "推荐附近好吃的川菜",
        "timestamp": "2026-07-19T14:30:00"
      },
      {
        "id": "msg_002",
        "role": "assistant",
        "content": "根据您的需求，我为您推荐以下餐厅：",
        "timestamp": "2026-07-19T14:31:00"
      }
    ]
  }
}
```

**错误响应**:

| code | message      |
|------|-------------|
| 404  | 对话不存在    |

---

### 7.3 创建对话

```
POST /api/conversations
```

**请求头**: `Authorization: Bearer {token}`

**请求体**:

| 字段  | 类型   | 必填 | 说明                 |
|-------|--------|------|---------------------|
| title | string | ❌   | 对话标题，默认"新对话" |

**成功响应** `201`:

```json
{
  "code": 0,
  "data": {
    "id": "conv_003",
    "title": "美食探索",
    "updated_at": "2026-07-19T15:00:00",
    "message_count": 0,
    "icon": "fas fa-comment"
  }
}
```

---

### 7.4 删除对话

```
DELETE /api/conversations/{conversation_id}
```

**请求头**: `Authorization: Bearer {token}`

**错误响应**:

| code | message      |
|------|-------------|
| 404  | 对话不存在    |

---

### 7.5 清空所有对话

```
DELETE /api/conversations
```

**请求头**: `Authorization: Bearer {token}`

**成功响应** `200`:

```json
{
  "code": 0,
  "message": "清空成功",
  "data": null
}
```

---

## 八、AI 模块（AI）—— 已有 + 增强

> **分支**: `feat/conversation`（对话集成）、`feat/ai-response-shop`（推荐卡片）
> **说明**: 后端已有 `/api/ai/*` 四项接口，但前端需要的是整合了对话管理和推荐卡片的统一聊天接口。

### 8.1 AI 对话（已有，需集成对话模块）

**当前实现**:

```
POST /api/ai/chat
```

**请求体**（后端当前参数）:

| 字段            | 类型    | 必填 | 说明                         |
|----------------|---------|------|-----------------------------|
| message        | string  | ✅   | 用户输入的消息               |
| conversation_id| string  | ❌   | 会话 ID，不传则新建会话       |
| stream         | boolean | ❌   | 是否流式返回                 |

**当前响应**:

```json
{
  "code": 0,
  "data": {
    "reply": "根据你的需求，我为你推荐几家不错的餐厅：...",
    "conversation_id": "conv_123"
  }
}
```

**增强建议 —— 整合对话 + 推荐卡片**:

为使前端能在一个接口完成"发消息 → 获得回复 + 推荐卡片"，建议改造 `POST /api/ai/chat` 响应，增加 `shop` 字段（可选）：

```json
{
  "code": 0,
  "data": {
    "reply": "根据您的需求，我为您推荐以下餐厅：",
    "conversation_id": "conv_001",
    "shop": {
      "id": "biz_001",
      "name": "蜀九香火锅",
      "image_url": "https://example.com/shop1.jpg",
      "rating": 4.8,
      "review_count": 326,
      "reason": "口碑极佳，环境舒适，性价比高",
      "price": "$$",
      "display_phone": "+86 28 88888888",
      "categories": [
        { "alias": "hotpot", "title": "火锅" }
      ],
      "location": {
        "address1": "锦江区春熙路88号",
        "city": "成都",
        "display_address": ["锦江区春熙路88号"]
      },
      "hours": null
    }
  }
}
```

> **与前端差异**:
> - 前端文档中 `shop` 字段有 `tags`（字符串数组），后端无对应字段，建议从 `categories` 提取 `title` 作为标签
> - 前端文档中 `shop.summary` 为评价摘要，后端 Business 模型没有该字段，可考虑从 `Review` 聚合生成
> - 前端文档中 `shop.price` 为整数，后端为字符串（`$` / `$$` / `$$$`）

---

### 8.2 AI 智能推荐（已有，后端内部接口）

```
POST /api/ai/recommend
```

**请求体**:

| 字段      | 类型   | 必填 | 说明         |
|-----------|--------|------|-------------|
| location  | string | ❌   | 地区         |
| cuisine   | string | ❌   | 菜系/口味    |
| budget    | string | ❌   | 预算         |
| occasion  | string | ❌   | 场景         |
| latitude  | float  | ❌   | 纬度         |
| longitude | float  | ❌   | 经度         |

**成功响应**:

```json
{
  "code": 0,
  "data": {
    "recommendations": [
      {
        "business_id": "biz_001",
        "name": "蜀九香火锅",
        "reason": "评分高，口碑好，是当地的人气之选"
      }
    ],
    "summary": "为你成都精选了 3 家优质餐厅，综合评分与口碑都很不错。"
  }
}
```

> **说明**: 此接口供前端"智能推荐"页面独立使用，也可作为 Chat 功能的底层数据源。

---

### 8.3 AI 评论总结（已有，前端未提及但建议暴露）

```
POST /api/ai/review-summary
```

**请求体**:

| 字段        | 类型   | 必填 | 说明         |
|-------------|--------|------|-------------|
| business_id | string | ✅   | 店铺 ID     |

**成功响应**:

```json
{
  "code": 0,
  "data": {
    "business_id": "biz_001",
    "business_name": "蜀九香火锅",
    "pros": ["味道正宗", "服务态度好", "环境干净整洁"],
    "cons": ["高峰期需要排队", "停车位较少"],
    "summary": "蜀九香火锅整体评价较好，主打地道口味..."
  }
}
```

> **前端未提，但建议增加**: 在商家详情页可集成"AI 总结"按钮，调用此接口快速展示口碑摘要。

---

### 8.4 AI 生成点评（已有，前端未提及但建议暴露）

```
POST /api/ai/generate-review
```

**请求体**:

| 字段        | 类型     | 必填 | 说明                                |
|-------------|----------|------|------------------------------------|
| business_id | string   | ✅   | 店铺 ID                            |
| rating      | int      | ❌   | 评分 1-5，默认 5                   |
| keywords    | string[] | ❌   | 关键词列表                          |
| style       | string   | ❌   | 风格：`normal` / `funny` / `professional` |

**成功响应**:

```json
{
  "code": 0,
  "data": {
    "content": "⭐ 5星 非常棒！\n\n味道、服务都很满意..."
  }
}
```

> **前端未提，但建议增加**: 在评论发布时可集成"AI 帮写"功能。

---

## 九、收藏模块（Favorite）—— ✅ 已完成

> **分支**: `feat/favorites`
> **说明**: 后端收藏功能已完成。新增 `favorites` 表（ORM 模型）、Pydantic Schema、Service 业务逻辑、Router API 端点，含完整单元测试套件。

### 9.1 获取收藏列表

```
GET /api/favorites
```

**请求头**: `Authorization: Bearer {token}`

**查询参数**:

| 字段      | 类型 | 必填 | 默认值 | 说明     |
|-----------|------|------|--------|---------|
| page      | int  | ❌   | 1      | 页码     |
| page_size | int  | ❌   | 20     | 每页条数 |

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "fav_001",
        "shop_id": "biz_001",
        "name": "蜀九香火锅",
        "image_url": "https://example.com/shop1.jpg",
        "rating": 4.8,
        "price": "$$",
        "address": "锦江区春熙路88号",
        "category": "火锅",
        "created_at": "2026-07-19T15:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

> **与前端差异**:
> - 前端用 `shopId`，后端建议用 `shop_id`
> - 前端用 `image`，后端用 `image_url`
> - 前端用 `price` 为整数，后端为字符串
> - 新增 `created_at` 字段记录收藏时间

---

### 9.2 添加收藏

```
POST /api/favorites
```

**请求头**: `Authorization: Bearer {token}`

**请求体**:

| 字段    | 类型   | 必填 | 说明     |
|---------|--------|------|---------|
| shop_id | string | ✅   | 商家 ID  |

**成功响应** `200`:

```json
{
  "code": 0,
  "message": "收藏成功",
  "data": {
    "id": "fav_001",
    "shop_id": "biz_001",
    "name": "蜀九香火锅",
    "image_url": "https://example.com/shop1.jpg",
    "rating": 4.8,
    "price": "$$",
    "address": "锦江区春熙路88号",
    "category": "火锅",
    "created_at": "2026-07-19T15:00:00"
  }
}
```

**错误响应**:

| code | message            |
|------|--------------------|
| 400  | 已收藏该商家        |
| 404  | 商家不存在          |

---

### 9.3 移除收藏

```
DELETE /api/favorites/{shop_id}
```

**请求头**: `Authorization: Bearer {token}`

**成功响应** `200`:

```json
{
  "code": 0,
  "message": "移除收藏成功",
  "data": null
}
```

**错误响应**:

| code | message          |
|------|------------------|
| 404  | 收藏不存在        |

---

## 十、管理后台模块（Admin）—— 待开发

> **分支**: `feat/admin`
> **说明**: 依赖认证模块，仅 `role=admin` 的用户可访问。

### 10.1 获取管理员信息

```
GET /api/admin/profile
```

**请求头**: `Authorization: Bearer {token}`

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "id": "u_admin",
    "username": "管理员",
    "avatar": "https://example.com/admin_avatar.jpg",
    "role": "admin"
  }
}
```

---

### 10.2 获取所有用户列表

```
GET /api/admin/users
```

**请求头**: `Authorization: Bearer {token}`

**查询参数**:

| 字段      | 类型   | 必填 | 默认值 | 说明                      |
|-----------|--------|------|--------|--------------------------|
| page      | int    | ❌   | 1      | 页码                      |
| page_size | int    | ❌   | 20     | 每页条数                  |
| keyword   | string | ❌   | —      | 搜索关键词（用户名）          |

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "u_abc123",
        "username": "张三",
        "email": "zhangsan@example.com",
        "bio": "热爱美食，分享生活",
        "avatar": "",
        "is_online": true,
        "register_time": "2026-07-15T14:30:00",
        "role": "user"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

**错误响应**:

| code | message      |
|------|-------------|
| 403  | 权限不足      |

> **与前端差异**: 前端文档中将 `password` 明文返回，**严禁如此**。后端返回列表中不应包含密码字段。

---

## 十一、健康检查（Health）—— 已有

```
GET /health
```

**说明**: 已有接口（`backend/routers/health.py`），用于前端连通性验证。

**成功响应** `200`:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "ok",
    "service": "TJLL API"
  }
}
```

---

## 十二、数据模型对齐

### 12.1 字段名映射（前端 ↔ 后端）

| 前端文档字段 | 后端字段         | 说明                         |
|-------------|-----------------|-----------------------------|
| `name`      | `username`      | 用户对象中的用户名            |
| `isOnline`  | `is_online`     | 是否在线                     |
| `registerTime` | `register_time` | ISO8601 格式，非 `YYYY-MM-DD` |
| `image`     | `image_url`     | 封面图/头像 URL              |
| `images`    | `photos`        | 图片列表                     |
| `lat`       | `latitude`      | 纬度                         |
| `lng`       | `longitude`     | 经度                         |
| `price`(int) | `price`(str)   | `$` / `$$` / `$$$`           |
| `shopId`    | `shop_id`       | 收藏中的商家 ID              |
| `conversationId` | `conversation_id` | 对话 ID                  |
| `time`      | `timestamp` / `updated_at` | ISO8601 格式       |

### 12.2 后端已有的额外字段（前端可按需使用）

| 模型      | 字段              | 类型     | 说明                       |
|-----------|------------------|----------|---------------------------|
| Business  | `alias`          | string   | Yelp 别名                  |
| Business  | `is_closed`      | boolean  | 是否已关闭                  |
| Business  | `url`            | string   | Yelp 原始链接              |
| Business  | `transactions`   | string[] | 服务类型（pickup/delivery） |
| Business  | `categories`     | Category[] | 分类对象 `{alias, title}` |
| Business  | `location`       | Location | 地址对象（含 city/state 等）|
| Business  | `coordinates`    | Coordinates | 坐标对象                  |
| Review    | `user`           | ReviewUser | 评论用户信息              |
| Review    | `url`            | string   | 评论原始链接               |
| AiResponse| `recommendations`| list     | 推荐列表                   |

### 12.3 需要新增的 ORM 模型

| 表名          | 说明           | 主要字段                                              |
|---------------|---------------|------------------------------------------------------|
| `app_users`   | 应用用户表     | id, username, password_hash, email, bio, avatar, is_online, role, register_time |
| `conversations` | 对话表       | id, user_id, title, icon, created_at, updated_at      |
| `messages`    | 消息表         | id, conversation_id, role, content, timestamp         |
| `favorites`   | 收藏表         | id, user_id, shop_id, created_at                      |

---

## 十三、错误码汇总

| code | 说明              |
|------|------------------|
| 0    | 成功              |
| 400  | 请求参数错误       |
| 401  | 未授权/认证失败    |
| 403  | 权限不足           |
| 404  | 资源不存在         |
| 409  | 资源冲突（如重复收藏）|
| 500  | 服务器内部错误     |

> **与前端差异**: 前端文档中 `200` = 成功、`201` = 创建成功。后端统一使用 `code: 0` 表示成功，HTTP 状态码保持语义（200 正常、201 创建、204 删除等）。
