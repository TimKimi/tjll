# ============================================================
# Justfile — 项目常用命令入口
# 用途：统一管理开发命令，避免记忆复杂的命令行参数
# 安装 just：https://github.com/casey/just
# 文档：https://just.systems/man/en/
# ============================================================

# ============================================================
# 设置
# ============================================================
set positional-arguments

# ============================================================
# 一、项目初始化
# ============================================================

# 安装所有依赖 + 安装 prek/pre-commit 钩子
# 新成员克隆项目后运行此命令即可开始开发
install:
    # 1. 安装 Python 依赖（uv 自动读取 pyproject.toml 的 dev 依赖）
    uv sync --all-groups
    # 2. 安装 pre-commit / prek git 钩子
    if command -v prek > /dev/null 2>&1; then prek install; else uv run pre-commit install; fi
    if command -v prek > /dev/null 2>&1; then prek install --hook-type commit-msg; else uv run pre-commit install --hook-type commit-msg; fi
    # 3. 成功提示
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

# 自动修复代码问题（ruff 自动修复 lint 错误）
fix:
    uv run ruff check --force-exclude --fix

# 检查代码格式是否正确（不修改文件）
fmt-check:
    uv run ruff format --force-exclude --check

# 自动格式化代码（ruff formatter 替代 black）
fmt:
    uv run ruff format --force-exclude

# Mypy 静态类型检查（仅后端，前端不含 Python）
mypy:
    uv run mypy backend

# Ty 类型检查（Astral 出品的快速类型检查器，可选）
ty:
    uv run ty check

# ============================================================
# 三、pre-commit / prek 相关
# ============================================================

# 运行所有钩子（作用于全部文件）
check:
    if command -v prek > /dev/null 2>&1; then prek run --all-files; else uv run pre-commit run --all-files; fi

# 手动更新钩子版本到最新
prek-update:
    if command -v prek > /dev/null 2>&1; then prek auto-update; else uv run pre-commit autoupdate; fi

# ============================================================
# 四、Commitizen 提交与版本管理
# ============================================================

# 交互式提交代码（推荐！自动引导你写符合规范的 commit 消息）
cz:
    uv run cz commit

# 查看提交规范帮助（列出所有可用 commit 类型：feat, fix, docs 等）
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
# 五、Git 推送 & 分支管理
# ============================================================

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

# 删除远程分支（合并后清理用）
# 用法：just branch-delete feat/user-auth
branch-delete branch:
    git push origin --delete {{ branch }}

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
