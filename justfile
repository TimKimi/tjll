# ============================================================
# TJLL 常用指令入口
# 用途：把复杂的多步操作变成一条命令
# 说明：justfile 只收录最常用的指令，完整清单见 docs/cli-reference.md
# 安装 just：https://github.com/casey/just
# ============================================================

set positional-arguments
set shell := ["sh", "-c"]


# ============================================================
# 安装
# ============================================================

# 首次初始化项目
# 作用：安装所有 Python 依赖 + 配置 git 提交前检查钩子
# 用法：just install
# 注意：新成员克隆仓库后先跑这条命令
install:
    uv sync --all-groups
    prek install --overwrite
    printf '#!/bin/sh\nexec uv run cz check --commit-msg-file "$@"\n' > .git/hooks/commit-msg


# ============================================================
# 代码质量检查
# ============================================================

# 全套代码检查（最常用）
# 自动执行：ruff 自动修复 → ruff 格式检查 → mypy 类型检查
# 用法：just lint
# 提示：提交前务必跑一次，确保 CI 不红
lint: fix fmt-check mypy

# ruff 自动修复 lint 问题（如未使用的导入、拼写错误等）
fix:
    uv run ruff check --force-exclude --fix

# ruff 格式化代码（修改文件缩进、空行等风格）
fmt:
    uv run ruff format --force-exclude

# 只检查格式是否正确，不修改文件（CI 流程用）
fmt-check:
    uv run ruff format --force-exclude --check

# mypy 类型检查（只扫描 backend/ 目录）
mypy:
    uv run mypy backend


# ============================================================
# 测试
# ============================================================

# 运行所有 pytest 测试（含单元测试 + 集成测试）
test:
    uv run pytest -c pyproject.toml -v --tb=short

# 只运行指定模块的测试
# 用法：just test-mod data              → 测试 data 模块
# 用法：just test-mod data_get          → 测试数据获取模块
# 用法：just test-mod data/test_loader  → 测试加载器转换函数
test-mod module:
    uv run pytest -c pyproject.toml backend/tests/{{ module }} -v --tb=short

# 只跑单元测试（不依赖数据库）
test-unit:
    uv run pytest -c pyproject.toml -m "not integration" -v --tb=short

# 只跑集成测试（依赖数据库）
test-integration:
    uv run pytest -c pyproject.toml -m integration -v --tb=short


# ============================================================
# 数据库（Docker PostgreSQL）
# ============================================================

# 启动 PostgreSQL 容器（后台运行）
db-up:
    docker compose up -d

# 停止 PostgreSQL 容器
db-down:
    docker compose down


# ============================================================
# Yelp 数据加载
# ============================================================

# 全量加载 Yelp 数据到 PostgreSQL（已有文件则跳过解压）
# 包含：商家 ~15 万条，评论 ~700 万条，支持断点续传
data-load:
    uv run python -m backend.scripts.extract_yelp_data

# 只加载 100 个商家 + 500 条评论（快速验证）
data-sample:
    uv run python -m backend.scripts.extract_yelp_data --max-businesses 100 --max-reviews 500

# 查看数据库中已加载的 Yelp 数据统计
data-check:
    uv run python -m backend.tests.scripts.check_db


# ============================================================
# 开发服务器
# ============================================================

# 启动 FastAPI 开发服务器（修改代码后自动重载）
serve:
    uv run uvicorn backend.main:app --reload

# 一条命令启动完整开发环境
# 自动先启动数据库，再启动开发服务器
up:
    docker compose up -d && uv run uvicorn backend.main:app --reload


# ============================================================
# 提交 & 推送
# ============================================================

# 交互式提交代码（自动引导填写 Conventional Commits 格式）
# 会提示选择类型（feat/fix/docs 等）、填写描述
cz:
    uv run cz commit

# 推送当前分支到远程（已关联远程的分支）
push:
    git push

# 首次推送新分支到远程（自动关联上下游）
# 用法：just push-u feat/user-auth
# 等价于：git push -u origin feat/user-auth
push-u branch:
    git push -u origin {{ branch }}


# ============================================================
# 分支管理流水线
# ============================================================

# 从 develop 分支拉取最新代码，并创建新功能分支
# 用法：just dev-branch feat/xxx
# 等价于依次执行：
#   git checkout develop
#   git pull
#   git checkout -b feat/xxx
dev-branch branch:
    git checkout develop
    git pull
    git checkout -b {{ branch }}

# 删除已完成的分支，并开启新功能分支
# 参数 1：要删除的旧分支名
# 参数 2：要创建的新分支名
# 用法：just del-branch feat/old-feat feat/new-feat
# 等价于依次执行：
#   git branch -d feat/old-feat
#   git push origin --delete feat/old-feat
#   git checkout develop && git pull
#   git checkout -b feat/new-feat
del-branch branch newbranch:
    git branch -d {{ branch }}
    git push origin --delete {{ branch }}
    git checkout develop
    git pull
    git checkout -b {{ newbranch }}

# 基于当前 HEAD 创建新分支（不切换分支）
# 用法：just new-branch feat/my-feature
new-branch branch:
    git checkout -b {{ branch }}


# ============================================================
# 依赖管理
# ============================================================

# 添加生产依赖
# 用法：just add fastapi
add pkg:
    uv add {{ pkg }}
