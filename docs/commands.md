# TJLL 命令行参考

> `just` 收录最常用指令；`uv run` / `docker` / `git` 等原生工具用于补充。
> 日常开发只需 `just lint` → `just cz` → `just push` 循环。

---

## just 指令

```bash
just install     # 首次初始化：安装依赖 + git 钩子
```

### 代码质量

```bash
just lint        # 全流程：自动修 lint → 格式检查 → mypy
just fix         # 仅 ruff 自动修复
just fmt         # ruff 格式化（修改文件）
just fmt-check   # 仅检查格式
just mypy        # 仅类型检查
```

### 测试

```bash
just test        # 全量 pytest
```

### 数据库

```bash
just db-up       # 启动 PostgreSQL 容器
just db-down     # 停止 PostgreSQL 容器

# 进阶：连接 psql
docker compose exec -T db psql -U tjll -d tjll
```

### Yelp 数据加载

```bash
just data-load 100 10    # 最多 100 商家，每商家至少 10 条有效评论
just data-sample          # 小批量验证（等价于 just data-load 5 1）
just data-check           # 查看数据库统计

# 仅解压（不加载）
uv run python -m backend.scripts.extract_yelp_data --skip-load

# 自定义参数
uv run python -m backend.scripts.extract_yelp_data \
    --max-businesses 100 \
    --min-reviews 20 \
    --batch-size 200
```

### 开发服务器

```bash
just serve       # 开发服务器（热重载）
just up          # 流水线：启动数据库 → 启动服务器
```

### 提交与推送

```bash
just cz                # 交互式提交（Conventional Commits）
just push              # 推送到当前远程分支
just push-u feat/xxx   # 首次推送新分支（关联远程）
```

### 分支管理

```bash
just dev-branch feat/xxx      # 从 develop 拉最新 + 创建新分支（一步到位）
just new-branch feat/xxx      # 基于当前 HEAD 创建本地分支
just del-branch old new       # 删除旧分支（本地+远程）并开启新功能
```

### 依赖管理

```bash
just add fastapi     # 添加生产依赖

# 以下操作未收入 justfile，直接用 uv：
uv add --dev pytest  # 添加开发依赖
uv remove fastapi    # 移除依赖
uv sync              # 同步依赖
uv tree              # 查看依赖树
uv lock --upgrade    # 升级所有依赖
uv outdated          # 查看过期依赖
```

---

## 数据加载细节

### 两阶段加载流程

```bash
# 1. 确保数据库运行
docker compose up -d

# 2. 加载数据（指定商家数和最低评论数）
just data-load 50 10
# 第一阶段：扫描 JSON，筛选商家/评论/用户
# 第二阶段：批量写入数据库

# 3. 验证
just data-check
```

### 字段映射

| 数据集字段 | 数据库字段 | 说明 |
|---|---|---|
| `business_id` → | `id` | 22 字符主键 |
| `stars` → | `rating` | review 为整数，business 为浮点数 |
| `is_open` (0/1) → | `is_closed` (bool) | `0` 表示已关闭 |
| `categories` (逗号字符串) → | `categories` (JSON) | 拆为 `[{alias, title}]` |
| `hours` (天名→时段) → | `business_hours` (JSON) | 转为 Yelp API 格式 |
| `address+city+state+postal_code` → | `address` (JSON) | 合并为 YelpLocation |
| `date` → | `time_created` | 直接映射 |
| `user_id` → | `user` (JSON) | 存为 `{"id": user_id}` |
| `user_id` + `name` + ... → | `users` 表 | 完整用户信息 |

### 代码接口（给其他模块调用）

```python
from backend.data.service import DataService

svc = DataService()
biz = await svc.get_business("some-id")
results, total = await svc.list_businesses(keyword="pizza", min_rating=4.0)
reviews, total = await svc.get_reviews_by_business("some-id")
stats = await svc.get_stats()
```

---

## 代码质量工具

```bash
# ruff
uv run ruff check --force-exclude --fix    # lint + 自动修
uv run ruff format --force-exclude          # 格式化

# mypy
uv run mypy backend                         # 类型检查

# pre-commit（钩子）
prek run --all-files                        # 运行所有钩子
git commit --no-verify                      # 紧急跳过钩子
```

---

## Git 操作

### 分支

```bash
just dev-branch feat/xxx        # 从 develop 拉最新 → 创建新分支
just new-branch feat/xxx        # 创建本地分支
just del-branch feat/old feat/new  # 清理旧分支 → 开启新功能

# 等价的原生命令：
git checkout -b feat/xxx                    # 新分支
git push -u origin feat/xxx                 # 首次推送
git branch -d feat/xxx                      # 删除本地分支
git push origin --delete feat/xxx           # 删除远程分支
```

### 版本发布

```bash
uv run cz bump --changelog                  # 自动版本号
uv run cz bump --increment patch --changelog
git push --tags                             # 推送 tag
```

---

## Docker

```bash
docker compose up -d                        # 启动
docker compose down                         # 停止
docker compose ps                           # 状态
docker compose logs -f db                   # 日志
docker compose exec -it db bash             # 进入容器
```
