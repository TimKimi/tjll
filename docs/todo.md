# 待办任务清单

> 项目开发任务总览，按优先级排序。

---

## 当前迭代 (feat/admin)

- [x] 创建项目架构文档 (`docs/architecture.md`)
- [x] 创建架构决策记录 (`docs/decision-records.md`)
- [x] 创建项目需求文档 (`docs/requirements.md`)
- [x] 创建开发日志 (`docs/development-log.md`)
- [x] 创建待办任务清单 (`docs/todo.md`)
- [x] 修正 `docs/api-need.md` 模块进度状态
- [x] 更新 `README.md` 补充文档索引
- [x] 实现 Admin 路由 — `GET /api/admin/profile`
- [x] 实现 Admin 路由 — `GET /api/admin/users`
- [x] 编写 Admin 模块单元测试
- [x] 注册 admin 路由到 `main.py`
- [x] 运行测试验证（41 路由测试全部通过）
- [ ] 提交代码（等待 review）

---

## 下一个迭代

- [ ] 对话管理模块（`feat/conversation`）
  - [ ] 创建 `Conversation` 和 `Message` ORM 模型
  - [ ] 对话 CRUD 接口
  - [ ] 对接 AI Chat

- [ ] 评论接口改造（`feat/review-api`）
  - [ ] 将 POST `/api/review/list` 改为 GET `/api/business/{business_id}/reviews`

- [ ] AI 推荐卡片增强（`feat/ai-response-shop`）
  - [ ] Chat 响应增加 Shop 对象

- [ ] 头像上传（`feat/avatar-upload`）
  - [ ] 文件存储
  - [ ] URL 回显

---

## 待评估

- [ ] 生产环境部署
- [ ] OSS/S3 对象存储集成
- [ ] Redis 对话历史缓存
- [ ] 管理员操作日志
- [ ] 用户封禁/解封功能
- [ ] 数据统计仪表盘
