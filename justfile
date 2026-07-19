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

# 首次初始化项目（安装依赖 + git 钩子）
install:
    uv sync --all-groups
    prek install --overwrite
    printf '#!/bin/sh\nexec uv run cz check --commit-msg-file "$@"\n' > .git/hooks/commit-msg


# ============================================================
# 代码质量检查
# ============================================================

# 快速代码检查：自动修复 lint + 格式化 + mypy
lint: fix fmt mypy

# 全量检查：lint + 测试覆盖率（CI 用）
check: lint coverage

# ruff 自动修复 lint 问题（未使用的导入、拼写错误等）
fix:
    uv run ruff check --force-exclude --fix

# ruff 自动格式化代码（缩进、空行等风格）
fmt:
    uv run ruff format --force-exclude

# 仅检查格式，不修改文件（CI 用）
fmtck:
    uv run ruff format --force-exclude --check

# mypy 类型检查（仅 backend/ 目录）
mypy:
    uv run mypy backend

# 单元测试 + 覆盖率报告（跳过集成测试）
coverage:
    uv run pytest -c pyproject.toml -m "not integration" -n auto --cov --cov-report=term-missing --cov-fail-under=60 -q --tb=short


# ============================================================
# 测试
# ============================================================

# 运行全部 pytest（含集成测试）
test:
    uv run pytest -c pyproject.toml -n auto -v --tb=short

# 运行指定模块测试：just tmod data
tmod module:
    uv run pytest -c pyproject.toml -n auto backend/tests/{{ module }} -v --tb=short

# 仅跑单元测试（不依赖数据库）
tunit:
    uv run pytest -c pyproject.toml -m "not integration" -n auto -v --tb=short

# 仅跑集成测试（依赖数据库）
tint:
    uv run pytest -c pyproject.toml -m integration -n auto -v --tb=short


# ============================================================
# 数据库（Docker PostgreSQL）
# ============================================================

# 启动 PostgreSQL 容器（后台运行）
dbup:
    docker compose up -d

# 停止 PostgreSQL 容器
dbdown:
    docker compose down


# ============================================================
# Yelp 数据加载
# ============================================================

# 两阶段加载 Yelp 数据集：just dload 100 50
dload biz rev:
    uv run python -m backend.scripts.extract_yelp_data --max-businesses {{ biz }} --min-reviews {{ rev }}

# 快速小批量加载（等价于 just dload 5 1）
dsample:
    uv run python -m backend.scripts.extract_yelp_data --max-businesses 5 --min-reviews 1

# 查看数据库中的 Yelp 数据统计
dstat:
    uv run python -m backend.tests.scripts.check_db


# ============================================================
# 离线评论清洗（可选；需本机 GGUF + llama.cpp，见 rag/models/.../README）
# ============================================================

# 离线清洗 Yelp 评论：just rvclean 5 10 0 0 5 200
rvclean biz rev shard start end maxrev="200":
    uv run python -m backend.rag.scripts.clean_yelp_reviews --max-businesses {{ biz }} --min-reviews {{ rev }} --shard {{ shard }} --start {{ start }} --end {{ end }} --max-reviews-per-business {{ maxrev }}


# ============================================================
# Yelp 数据 → OpenSearch 入库
# ============================================================

# 补写：入库 index_progress 里缺失的商家
idx-backfill:
    uv run python -m backend.rag.scripts.index_cleaned_yelp --mode backfill

# 复写：全部商家重新入库（同 chunk_id 覆盖旧数据）
idx-rewrite:
    uv run python -m backend.rag.scripts.index_cleaned_yelp --mode rewrite

# 兼容旧名，默认补写
idx-clean:
    uv run python -m backend.rag.scripts.index_cleaned_yelp --mode backfill

# 删除索引并重建后复写
idx-recreate:
    uv run python -m backend.rag.scripts.index_cleaned_yelp --mode rewrite --recreate


# ============================================================
# 开发服务器
# ============================================================

# 启动 FastAPI 开发服务器（热重载）
serve:
    uv run uvicorn backend.main:app --reload

# 一键启动完整环境（数据库 + 服务器）
up:
    docker compose up -d && uv run uvicorn backend.main:app --reload


# ============================================================
# 提交 & 推送
# ============================================================

# 交互式提交代码（Conventional Commits 格式）
cz:
    uv run cz commit

# 推送当前分支到远程
push:
    git push

# 首次推送新分支到远程：just pushu feat/user-auth
pushu branch:
    git push -u origin {{ branch }}


# ============================================================
# 分支管理
# ============================================================

# 同步 develop 并创建新功能分支：just cob feat/xxx
cob branch:
    git checkout develop
    git pull
    git checkout -b {{ branch }}

# 删除本地+远程分支后同步 develop 并建新分支：just brdel feat/old feat/new
brdel branch newbranch:
    git branch -d {{ branch }}
    git push origin --delete {{ branch }}
    git checkout develop
    git pull
    git checkout -b {{ newbranch }}

# 基于当前 HEAD 创建新分支（不自动切换）：just brnew feat/xxx
brnew branch:
    git branch {{ branch }}


# ============================================================
# 依赖管理
# ============================================================

# 添加生产依赖：just add fastapi
add pkg:
    uv add {{ pkg }}
