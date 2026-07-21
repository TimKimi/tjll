# 待办任务清单

> 项目开发任务总览，按优先级排序。

---

## 当前迭代 (feat/avatar-upload)

- [ ] 实现头像上传 — `POST /api/user/avatar`
- [ ] 实现头像上传 Service 逻辑
- [ ] 编写头像上传单元测试
- [ ] 运行测试验证

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
