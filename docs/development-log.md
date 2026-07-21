# 开发日志

> 记录项目开发过程中的重要节点、问题和决策。

---

## [2026-07-21] feat/admin 分支开发

### 已完成
- 创建 `docs/architecture.md` — 项目架构文档
- 创建 `docs/decision-records.md` — 架构决策记录
- 创建 `docs/requirements.md` — 项目需求文档
- 创建 `docs/todo.md` — 待办任务清单
- 修正 `docs/api-need.md` — 同步各模块实际进度状态
- 更新 `README.md` — 补充关键文档索引

### 已完成
- 创建 `backend/schemas/admin.py` — Admin Pydantic Schema
- 创建 `backend/services/admin.py` — AdminService 业务逻辑
- 创建 `backend/routers/admin.py` — Admin 路由（profile + users）
- 注册 admin 路由到 `backend/main.py`
- 创建 `backend/tests/test_routers/test_admin.py` — Admin 模块单元测试（6 个测试用例）

### 待验证
- 运行测试套件确认通过

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
