# Yelp API 接口文档

> 基于 Yelp Places API (Fusion) 提取本项目所需的接口。
>
> 官方文档：https://docs.developer.yelp.com/docs/getting-started

---

## 目录

- [通用说明](#通用说明)
- [接口概览](#接口概览)
- [1. Business Search](#1-business-search)
- [2. Business Details](#2-business-details)
- [3. Reviews](#3-reviews)
- [通用错误码](#通用错误码)
- [注意事项](#注意事项)

---

## 通用说明

### 认证方式

所有请求需要在 Header 中携带 API Key：

```
Authorization: Bearer <YOUR_API_KEY>
```

### 基础 URL

```
https://api.yelp.com/v3
```

### 关于"商品"数据的说明

Yelp Places API **不提供独立的商品/产品列表接口**。商家的经营类别通过 `categories` 字段表示。对于餐厅类商家，Business Details（Premium 套餐）会返回 `yelp_menu_url`（菜单链接），但无结构化菜单数据。

如果项目需要商家下的具体商品/服务数据，后续可能需要爬取或通过 Yelp 页面解析补充。

---

## 接口概览

| # | 接口 | 方法 | 用途 |
|---|---|---|---|
| 1 | `/v3/businesses/search` | GET | 搜索商家，返回基本信息列表 |
| 2 | `/v3/businesses/{id}` | GET | 获取单个商家的详细信息 |
| 3 | `/v3/businesses/{id}/reviews` | GET | 获取商家的评论列表 |

---

## 1. Business Search

搜索商家，返回最多 **240** 个结果。

> **注意：** API 不返回没有评论的商家。

### 请求

```
GET https://api.yelp.com/v3/businesses/search
```

#### 请求参数（Query）

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `location` | string | 条件必填 | 地理区域，如 "New York City"。`latitude`/`longitude` 未提供时必填 |
| `latitude` | number | 条件必填 | 纬度 (-90 ~ 90)，与 `longitude` 一起提供时可替代 `location` |
| `longitude` | number | 条件必填 | 经度 (-180 ~ 180) |
| `term` | string | 否 | 搜索词，如 "food"、"Starbucks"。最大 300 字符 |
| `radius` | integer | 否 | 搜索半径（米），最大 40000（约 25 英里） |
| `categories` | array | 否 | 分类过滤，逗号分隔，如 `"bars,french"` |
| `locale` | string | 否 | 语言代码，如 `en_US`、`zh_TW` |
| `price` | array | 否 | 价格过滤，1=$ ~ 4=$$$$ |
| `open_now` | boolean | 否 | 只返回正在营业的商家 |
| `open_at` | integer | 否 | Unix 时间戳，返回该时间正在营业的商家 |
| `sort_by` | string | 否 | 排序：`best_match`（默认）、`rating`、`review_count`、`distance` |
| `limit` | integer | 否 | 返回数量（0~50，默认 20） |
| `offset` | integer | 否 | 偏移量（0~1000） |

### 成功响应 (200)

```json
{
  "businesses": [
    {
      "id": "QPOI0dYeAl3U8iPM_IYWnA",
      "alias": "golden-boy-pizza-hamburg",
      "name": "Golden Boy Pizza",
      "image_url": "https://...",
      "is_closed": false,
      "url": "https://www.yelp.com/biz/...",
      "review_count": 903,
      "categories": [
        { "alias": "pizza", "title": "Pizza" },
        { "alias": "food", "title": "Food" }
      ],
      "rating": 4.0,
      "coordinates": {
        "latitude": 41.7873,
        "longitude": -123.0515
      },
      "transactions": ["pickup", "delivery"],
      "price": "$",
      "location": {
        "address1": "James",
        "address2": "Street",
        "address3": "68M",
        "city": "Los Angeles",
        "state": "CA",
        "zip_code": "22399",
        "country": "US",
        "display_address": ["James", "Street", "68M", "Los Angeles, CA 22399"]
      },
      "phone": "+14159829738",
      "display_phone": "(415) 982-9738",
      "distance": 4992.44,
      "business_hours": {
        "open": [
          { "is_overnight": false, "start": "0900", "end": "2100", "day": 0 }
        ],
        "hours_type": "REGULAR",
        "is_open_now": true
      }
    }
  ],
  "total": 6800,
  "region": {
    "center": {
      "latitude": 37.7609,
      "longitude": -122.4364
    }
  }
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `businesses[].id` | string | Yelp 商家唯一 ID（22 字符） |
| `businesses[].alias` | string | Yelp 商家别名，可含 unicode |
| `businesses[].name` | string | 商家名称 |
| `businesses[].image_url` | string | 商家封面图片 URL |
| `businesses[].is_closed` | boolean | 商家是否已永久关闭 |
| `businesses[].url` | string | Yelp 商家页面 URL |
| `businesses[].review_count` | integer | 评论总数 |
| `businesses[].categories` | array | 分类列表（`alias` + `title`） |
| `businesses[].rating` | decimal | 评分（1, 1.5, ..., 5） |
| `businesses[].coordinates` | object | 经纬度 |
| `businesses[].price` | string | 价格等级（$ / $$ / $$$ / $$$$） |
| `businesses[].location` | object | 地址信息 |
| `businesses[].phone` | string | 原始电话号码 |
| `businesses[].display_phone` | string | 格式化后电话号码 |
| `businesses[].distance` | decimal | 距搜索点的距离（米） |
| `businesses[].business_hours` | object | 营业时间 |
| `total` | integer | 匹配总数 |
| `region.center` | object | 搜索结果区域的中心点 |

### 错误响应 (400 ~ 503)

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "description": "Invalid Request"
  }
}
```

常见 HTTP 状态码：400、401、403、404、413、429、500、503。

---

## 2. Business Details

获取单个商家的**详细信息**，比 Search 返回更多字段。

> 需要先从 Search 拿到 `business_id` 或 `alias`。

### 请求

```
GET https://api.yelp.com/v3/businesses/{business_id_or_alias}
```

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `business_id_or_alias` | string | 是 | Yelp 商家 ID（22 字符）或 alias |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `locale` | string | 否 | 语言代码 |

### 成功响应 (200)

响应包含 Search 中所有字段（同上），**额外增加以下字段**：

```json
{
  "id": "QPOI0dYeAl3U8iPM_IYWnA",
  "alias": "golden-boy-pizza-hamburg",
  "name": "Golden Boy Pizza",
  "image_url": "https://...",
  "is_claimed": false,
  "is_closed": false,
  "url": "https://...",
  "review_count": 903,
  "categories": [
    { "alias": "pizza", "title": "Pizza" }
  ],
  "rating": 4.0,
  "coordinates": {
    "latitude": 41.7873,
    "longitude": -123.0515
  },
  "price": "$",
  "location": { "...": "..." },
  "phone": "+14159829738",
  "display_phone": "(415) 982-9738",
  "photos": [
    "https://...photo1.jpg",
    "https://...photo2.jpg",
    "https://...photo3.jpg"
  ],
  "hours": {
    "open": [
      { "is_overnight": false, "start": "0900", "end": "2100", "day": 0 }
    ],
    "hours_type": "REGULAR",
    "is_open_now": true
  },
  "special_hours": [
    {
      "date": "2019-02-07",
      "start": "1600",
      "end": "2000",
      "is_overnight": false,
      "is_closed": null
    }
  ],
  "transactions": ["pickup", "delivery"],
  "messaging": {
    "url": "https://...",
    "use_case_text": "Request a Quote",
    "response_rate": 1.0,
    "response_time": 791,
    "is_enabled": true
  }
}
```

#### Search 中不存在的额外字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `is_claimed` | boolean | 商家是否已被认领 |
| `photos` | array[string] | 商家照片 URL（最多 3 张，Premium 最多 12 张） |
| `hours` | object | 营业时间（结构化，含每日时段） |
| `special_hours` | array | 特殊营业时间（节假日等） |
| `messaging` | object | 商家消息/询价功能信息 |

#### Premium 套餐才有的字段

| 字段 | 说明 |
|---|---|
| `photo_details` | 照片详情（ID、宽高、标签等） |
| `photo_count` | 照片总数 |
| `yelp_menu_url` | 商家菜单 URL |
| `attributes` | 商家属性（素食友好、户外座位等） |
| `popularity_score` | 人气评分（按同品类） |
| `licenses` | 营业执照信息 |

### 错误响应

格式同 Search：`{ "error": { "code": "...", "description": "..." } }`

---

## 3. Reviews

获取某个商家的评论列表。按 Yelp 默认排序返回。

> **注意：**
> - 基础套餐最多返回 **3 条**评论（且为摘要 excerpt）
> - 需要 **Enhanced 或 Premium Plan** 才能访问
> - API 不返回没有评论的商家

### 请求

```
GET https://api.yelp.com/v3/businesses/{business_id_or_alias}/reviews
```

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `business_id_or_alias` | string | 是 | Yelp 商家 ID 或 alias |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `locale` | string | 否 | 语言代码 |
| `offset` | integer | 否 | 偏移量（0~1000） |
| `limit` | integer | 否 | 返回数量（0~50，默认 20） |
| `sort_by` | string | 否 | 固定为 `yelp_sort` |

### 成功响应 (200)

```json
{
  "total": 3,
  "reviews": [
    {
      "id": "xAG4O7l-t1ubbwVAlPnDKg",
      "url": "https://www.yelp.com/biz/...",
      "text": "Went back again to this place since the last time...",
      "rating": 5,
      "time_created": "2016-08-29 00:41:13",
      "user": {
        "id": "W8UK02IDdRS2GL_66fuq6w",
        "profile_url": "https://www.yelp.com/user_details?...",
        "image_url": "https://...",
        "name": "Ella A."
      }
    }
  ],
  "possible_languages": ["en"]
}
```

#### 响应字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `reviews[].id` | string | 评论唯一 ID |
| `reviews[].url` | string | Yelp 上该评论的链接 |
| `reviews[].text` | string | 评论文本内容 |
| `reviews[].rating` | int | 评分（1~5） |
| `reviews[].time_created` | string | 创建时间（格式：`YYYY-MM-DD HH:mm:ss`） |
| `reviews[].user.id` | string | 用户 ID |
| `reviews[].user.profile_url` | string | 用户 Yelp 主页 |
| `reviews[].user.image_url` | string | 用户头像 URL（可能为空） |
| `reviews[].user.name` | string | 用户昵称（名+姓首字母） |
| `total` | integer | 返回的评论数 |
| `possible_languages` | array | 该商家评论支持的语言列表 |

### 错误响应 (400 ~ 503)

```json
{
  "error": {
    "code": "NOT_FOUND",
    "description": "Resource Not Found"
  }
}
```

其他错误码示例：

| HTTP 状态码 | code | 说明 |
|---|---|---|
| 400 | `INVALID_REQUEST` | 请求参数错误 |
| 401 | `UNAUTHORIZED_API_KEY` | API Key 无权访问 |
| 401 | `TOKEN_INVALID` | API Key 无效 |
| 403 | `AUTHORIZATION_ERROR` | 无权限 |
| 404 | `NOT_FOUND` | 资源不存在 |
| 429 | `TOO_MANY_REQUESTS_PER_SECOND` | 超过频率限制 |
| 500 | `INTERNAL_ERROR` | Yelp 服务端错误 |
| 503 | `SERVICE_UNAVAILABLE` | 服务不可用 |

---

## 通用错误码

所有 Yelp API 端点返回的错误使用以下结构：

```json
{
  "error": {
    "code": "<ERROR_CODE>",
    "description": "<Description>"
  }
}
```

| HTTP 状态码 | error_code | 说明 |
|---|---|---|
| 400 | `INVALID_REQUEST` | 请求参数不合法 |
| 400 | `VALIDATION_ERROR` | 参数校验失败 |
| 400 | `FIELD_REQUIRED` | 缺少必填字段 |
| 401 | `UNAUTHORIZED_API_KEY` | API Key 无权限 |
| 401 | `TOKEN_INVALID` | API Key 格式错误或已失效 |
| 403 | `AUTHORIZATION_ERROR` | 功能未授权 |
| 404 | `NOT_FOUND` | 资源不存在 |
| 413 | `PAYLOAD_TOO_LARGE` | 请求体过大 |
| 429 | `TOO_MANY_REQUESTS_PER_SECOND` | 频率超限 |
| 429 | `DAILY_QUOTA_EXCEEDED` | 日配额超限 |
| 500 | `INTERNAL_ERROR` | Yelp 内部错误 |
| 503 | `SERVICE_UNAVAILABLE` | Yelp 服务暂不可用 |

---

## 注意事项

### 1. 数据量限制

| 端点 | 限制 |
|---|---|
| Business Search | 最多返回 **240** 个商家，单次最多 50 |
| Business Details | 无特别限制 |
| Reviews | 基础套餐仅 **3 条**，需要更高套餐才能返回更多 |

### 2. 不会返回评论的商家

如果商家没有评论，三个端点都不会返回该商家。

### 3. 价格套餐

| 套餐 | 可访问的字段 |
|---|---|
| 基础 (Free) | Search 基本字段 + Details 基本字段 |
| Enhanced | Reviews 端点 + 更多照片 |
| Premium | `photo_details`、`yelp_menu_url`、`attributes`、`popularity_score`、`licenses` 等 |

### 4. 限流

Yelp Places API 按日配额 + 每秒查询数双重限流，具体配额取决于套餐。

### 5. 搜索结果的排序

- `sort_by=rating` 并非严格按评分排序，而是用贝叶斯平均调整（防止单条高分评论的商家排到前面）
- `sort_by` 只是**建议**，Yelp 搜索引擎综合考虑多个参数
