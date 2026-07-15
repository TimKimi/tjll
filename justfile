# ============================================================
# Justfile — 项目常用命令入口
# 用途：统一管理开发命令，避免记忆复杂的命令行参数
# 安装 just：https://github.com/casey/just
# 文档：https://just.systems/man/en/
# ============================================================

# ============================================================
# 设置
# Windows 下默认的 sh 来自 Git Bash（Git 安装自带）
# ============================================================
set positional-arguments
set shell := ["sh", "-c"]

# ============================================================
# 一、项目初始化
# ============================================================

# 安装所有依赖 + 安装 prek/pre-commit 钩子
# 新成员克隆项目后运行此命令即可开始开发
install:
    uv sync --all-groups
    # 1. 安装 pre-commit 阶段钩子
    prek install --overwrite
    # 2. 手动创建 commit-msg 钩子，绕过 prek（Windows 上 prek 的 commit-msg 有 bug）
    printf '#!/bin/sh\nexec uv run cz check --commit-msg-file "$@"\n' > .git/hooks/commit-msg
    @echo ""
    @echo "============================================"
    @echo "  ✓ 安装完成！"
    @echo "  使用 just cz       交互式提交代码"
    @echo "  使用 just lint     手动运行代码质量检查"
    @echo "  使用 just check    运行所有 pre-commit 钩子"
    @echo "============================================"

# ============================================================
# 二、代码质量检查（lint / format / type-check）
# ============================================================

# 运行所有代码检查（自动修复 + 格式检查 + 类型检查）
lint: fix fmt-check mypy ty
    @echo "✓ 所有代码检查通过！"

# ruff 自动修复 lint 问题
fix:
    uv run ruff check --force-exclude --fix

# 检查代码格式（不修改文件）
fmt-check:
    uv run ruff format --force-exclude --check

# 自动格式化代码
fmt:
    uv run ruff format --force-exclude

# Mypy 后端类型检查
mypy:
    uv run mypy backend

# Ty 类型检查（可选）
ty:
    uv run ty check

# ============================================================
# 七、测试
# ============================================================

# 运行单元测试（不调真实 API）
test-unit:
    uv run pytest -c pyproject.toml -m "not integration" -v --tb=short

# 运行集成测试（调 Yelp 真实 API + 数据库）
test-integration:
    uv run pytest -c pyproject.toml -m integration -v --tb=short

# 全量测试（单元 + 集成）
test: test-unit test-integration


# ============================================================
# 三、pre-commit / prek 相关
# ============================================================

# 运行所有钩子（作用于全部文件）
check:
    prek run --all-files

# 手动更新钩子版本到最新
prek-update:
    prek auto-update

# ============================================================
# 四、Commitizen 提交与版本管理
# ============================================================

# 交互式提交代码（自动引导符合规范的 commit 消息）
cz:
    uv run cz commit

# 查看提交规范帮助
cz-help:
    uv run cz schema

# 版本发布：自动更新版本号 + 生成 CHANGELOG.md + 创建 git tag
# 用法：
#   just cz-bump          自动推断版本增量
#   just cz-bump patch    手动指定修订号
#   just cz-bump minor    手动指定次版本号
# just cz-bump major    手动指定主版本号
cz-bump increment="":
    uv run cz bump{{ if increment != "" { " --increment=" + increment } else { "" } }} --changelog

# 查看当前版本号
show-version:
    uv run cz version

# ============================================================
# 五、Git 操作 & 分支管理
# ============================================================

# 切到 develop 分支并拉取最新
dev-pull:
    git checkout develop
    git pull

# 创建你本地的分支
new-branch branch:
    git checkout -b {{ branch }}

# 拉取dev分支到最新并从dev分支创建本地分支
dev-branch branch:
    just dev-pull
    just new-branch {{ branch }}

# 删除本地及远程已完成的分支，并拉取dev分支到最新并创建新分支
del-branch branch newbranch:
    git branch -d {{ branch }}
    just branch-delete {{ branch }}
    just dev-branch {{ newbranch }}

# 推送当前分支到远程
push:
    git push

# 首次推送新分支（自动关联远程）
# 用法：just push-u feat/user-auth
push-u branch:
    git push -u origin {{ branch }}

# 推送并同时推送 tag（版本发布时使用）
push-tags:
    git push
    git push --tags

# 删除远程分支
# 用法：just branch-delete feat/user-auth
branch-delete branch:
    git push origin --delete {{ branch }}

# ============================================================
# 七、后端开发
# ============================================================

# 启动后端开发服务器（热重载）
serve:
    uv run uvicorn backend.main:app --reload


# ============================================================
# 六、依赖管理
# ============================================================

# 添加生产依赖：just add requests
add pkg:
    uv add {{ pkg }}

# 添加开发依赖：just add-dev pytest
add-dev pkg:
    uv add --dev {{ pkg }}

# 移除依赖：just remove requests
remove pkg:
    uv remove {{ pkg }}

# 升级所有依赖到最新兼容版本
uv-upgrade:
    uv lock --upgrade

# 查看过期的依赖
uv-outdated:
    uv outdated
