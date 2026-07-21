# 开发日志

> 记录项目开发过程中的重要节点、问题和决策。

---

## [2026-07-21] feat/avatar-upload 分支开发

### 开发中
- 实现头像上传接口（`POST /api/user/avatar`）

---

## [2026-07-19] feat/favorites 分支合并

将收藏模块合并至 develop：
- 新增 `Favorite` ORM 模型
- 新增 `FavoriteItem` / `AddFavoriteRequest` Schema
- 新增 `FavoriteService` 业务逻辑
- 新增 `favorite.py` 路由
- 含完整单元测试套件

---

## [2026-07-15] feat/user-auth 分支合并

将认证与用户模块合并至 develop：
- 新增 `AppUser` ORM 模型
- 新增 Auth 路由（注册/登录/管理员登录/退出）
- 新增 User 路由（获取/更新个人信息）
- JWT 签发与验证中间件
- 密码 bcrypt 哈希存储

---

## [2026-07-10] API 需求文档对齐

对齐前端需求与后端实现：
- 确定统一响应格式 `ApiResponse[T]`
- 字段映射确认（snake_case ↔ camelCase）
- 新增开发分支规划

---

## [2026-07-01] 项目初始化

- 搭建 FastAPI 后端框架
- 配置 Ruff、mypy、pre-commit 代码质量工具链
- 配置 Commitizen 约定式提交
- 配置 GitHub Actions CI
- 加载 Yelp 学术数据集
- 搭建 RAG 管道（LangChain + OpenSearch + BGE）
