#!/usr/bin/env python3
"""生成测试用例文档（Markdown）。

从 backend/tests/ 下解析所有 pytest 测试函数，提取类名、函数名、docstring、
装饰器等信息，按模块分组输出为标准化的测试用例表格。

用法:
    python generate_test_docs.py                        # 默认中文
    python generate_test_docs.py --lang en              # 英文（自动调用 LLM 翻译）
    python generate_test_docs.py --output docs/test-cases.md
    python generate_test_docs.py --lang en --no-translate  # 英文，不翻译（仅清洗）
"""

from __future__ import annotations

import argparse
import ast
import itertools
import os
import re
import sys
from typing import Any, cast
from pathlib import Path

from backend.config import settings

try:
    from openai import OpenAI as _OpenAI

    _HAVE_OPENAI = True
except ImportError:
    _OpenAI: Any = None
    _HAVE_OPENAI = False

# ── 路径 ───────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent
TEST_DIR = REPO_ROOT / "backend" / "tests"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "test-cases.md"

# ── 模块分类映射 ────────────────────────────────────────────────────────────

MODULE_MAP: dict[str, str] = {
    "test_routers": "路由",
    "test_services": "服务",
    "test_data": "数据",
    "test_schemas": "Schema",
    "test_models": "模型",
    "test_llm": "LLM",
    "test_rag": "RAG",
    "test_core": "核心",
    "test_utils": "工具",
}

# 用于从 AST 判断测试类型的标记
_INTEGRATION_MARKERS = {"integration"}
_ASYNCIO_MARKER = "asyncio"


# ── AST 解析 ────────────────────────────────────────────────────────────────


def _extract_decorator_names(
    decorators: list[ast.expr],
) -> list[str]:
    """从装饰器 AST 节点提取可读名称列表。

    处理:
      @pytest.mark.asyncio        → ["asyncio"]
      @patch("xxx.xxx")           → ["patch(xxx.xxx)"]
      @pytest.mark.integration    → ["integration"]
    """
    names: list[str] = []
    for d in decorators:
        if isinstance(d, ast.Call):
            # @patch("path") 或 @pytest.mark.asyncio()
            func = d.func
            if isinstance(func, ast.Attribute):
                base = (
                    _ast_name(func.value)
                    if isinstance(func.value, ast.Attribute | ast.Name)
                    else ""
                )
                parts = []
                if base:
                    parts.append(base)
                parts.append(func.attr)
                joined = ".".join(parts)
                args = [ast.unparse(a) for a in d.args]
                kwargs = [f"{k.arg}={ast.unparse(k.value)}" for k in d.keywords]
                all_args = ", ".join(itertools.chain(args, kwargs))
                names.append(f"{joined}({all_args})")
            elif isinstance(func, ast.Name):
                args = [ast.unparse(a) for a in d.args]
                kwargs = [f"{k.arg}={ast.unparse(k.value)}" for k in d.keywords]
                all_args = ", ".join(itertools.chain(args, kwargs))
                names.append(f"{func.id}({all_args})")
        elif isinstance(d, ast.Attribute):
            # @pytest.mark.asyncio (无括号)
            base = (
                _ast_name(d.value)
                if isinstance(d.value, ast.Attribute | ast.Name)
                else ""
            )
            if base:
                names.append(f"{base}.{d.attr}")
            else:
                names.append(d.attr)
        elif isinstance(d, ast.Name):
            names.append(d.id)
    return names


def _ast_name(node: ast.expr) -> str:
    """从 AST 节点提取名字（支持 Name 和 Attribute 链）。"""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_ast_name(node.value)}.{node.attr}"
    return ""


def _clean_docstring(doc: str) -> str:
    """清洗 docstring：去前缀、去空白、取第一段。"""
    if not doc:
        return ""
    # 只取第一段
    doc = doc.strip().split("\n\n")[0].strip()
    # 去掉常见前缀
    doc = re.sub(r"^(测试|验证|检查)\s*", "", doc)
    doc = re.sub(r"^[「『【]?", "", doc)
    doc = doc.strip()
    return doc


def _infer_description(func_name: str, doc: str, lang: str) -> str:
    """从函数名反推描述（当 docstring 为空时）。"""
    if doc:
        return doc
    # snake_case -> 中文/英文自然语言
    name = func_name
    if name.startswith("test_"):
        name = name[5:]
    words = name.split("_")
    if lang == "zh":
        return " ".join(words)  # 保留原始 snake_case，用户可读
    return " ".join(w.capitalize() for w in words)


def _classify_test(
    decorator_names: list[str],
    imports: set[str],
) -> str:
    """根据装饰器和导入判断测试类型。"""
    # 去掉 pytest.mark. 前缀后检查
    simple_names = {d.replace("pytest.mark.", "") for d in decorator_names}

    if simple_names & _INTEGRATION_MARKERS:
        return "集成"
    if any("patch(" in d for d in decorator_names):
        return "Mock外部API"
    if _ASYNCIO_MARKER in simple_names:
        if "AsyncMock" in imports or "mock_db" in imports:
            return "Mock服务"
        return "集成"
    return "纯单元"


def _detect_imports(tree: ast.AST) -> set[str]:
    """收集文件中所有 import 的名称（简化）。"""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
                names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                full = alias.name
                names.add(full)
                if alias.asname:
                    names.add(alias.asname)
                # 如果 from xxx import mock_db
                if full == "mock_db":
                    names.add("mock_db")
    return names


# ── 遍历与解析 ──────────────────────────────────────────────────────────────


def _walk_tests() -> list[dict]:
    """遍历测试目录，解析所有测试函数。

    返回列表，每项含:
      module, file, class_name, func_name, description, decorators, test_type
    """
    rows: list[dict] = []
    test_root = TEST_DIR.resolve()

    for py_file in sorted(test_root.rglob("test_*.py")):
        rel = py_file.relative_to(test_root)
        parts = rel.parts
        # 确定模块
        if len(parts) > 1:
            dir_name = str(parts[0])
            module = MODULE_MAP.get(dir_name, dir_name)
        else:
            module = "核心"

        file_name = py_file.name
        content = py_file.read_text(encoding="utf-8")

        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue

        imports = _detect_imports(tree)

        # 只遍历顶级节点（避免类内函数被重复匹配）
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                if not class_name.startswith("Test"):
                    continue
                for item in node.body:
                    if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                        if not item.name.startswith("test_"):
                            continue
                        doc = ast.get_docstring(item) or ""
                        decorators = _extract_decorator_names(item.decorator_list)
                        rows.append(
                            _make_row(
                                module,
                                file_name,
                                class_name,
                                item,
                                content,
                                doc,
                                decorators,
                                imports,
                            )
                        )
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if not node.name.startswith("test_"):
                    continue
                doc = ast.get_docstring(node) or ""
                decorators = _extract_decorator_names(node.decorator_list)
                rows.append(
                    _make_row(
                        module,
                        file_name,
                        None,
                        node,
                        content,
                        doc,
                        decorators,
                        imports,
                    )
                )

    return rows


def _make_row(
    module: str,
    file_name: str,
    class_name: str | None,
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    source: str,
    doc: str,
    decorators: list[str],
    imports: set[str],
) -> dict:
    func_name = func_node.name
    cleaned_doc = _clean_docstring(doc)
    test_type = _classify_test(decorators, imports)

    # 提取函数源代码（含装饰器行）
    func_source = ast.get_source_segment(source, func_node) or ""

    # 筛选有意义的标记（去掉 pytest.mark. 前缀，合并同类项）
    markers = []
    for d in decorators:
        if d.startswith("pytest.mark."):
            markers.append(d.replace("pytest.mark.", ""))
        elif d.startswith("patch("):
            markers.append("patch")
        else:
            markers.append(d)
    markers_str = ", ".join(sorted(set(markers))) if markers else ""

    return {
        "module": module,
        "file": file_name,
        "class": class_name or "-",
        "func": func_name,
        "source": func_source,
        "description": cleaned_doc or "",
        "markers": markers_str,
        "type": test_type,
    }


# ── LLM 描述增强 ─────────────────────────────────────────────────────


def _batch_enrich(
    rows: list[dict],
    lang: str,
    api_key: str,
    base_url: str = "",
    model: str = "deepseek-v4-flash",
) -> None:
    """用 LLM 批量生成/翻译测试函数描述的增强版。

    对每一条 row，将函数源码 + 原始描述发给 LLM，
    让 LLM 理解代码逻辑后，用 {lang} 重新生成简洁、精准的描述。
    直接原地修改 rows 中的 "description" 字段。
    """
    if not api_key:
        return
    if not rows:
        return
    if not _HAVE_OPENAI:
        print("[WARN] openai 库未安装，跳过 LLM 增强", file=sys.stderr)
        return

    # 分出需要 LLM 处理的：
    #   zh 模式：只有空描述或描述 = 函数名的需要生成
    #   en 模式：全部需要翻译/生成
    need_llm: list[tuple[int, dict]] = []
    for i, r in enumerate(rows):
        if lang == "en":
            need_llm.append((i, r))
        elif not r["description"] or r["description"] == r["func"]:
            need_llm.append((i, r))

    if not need_llm:
        return

    client = _OpenAI(
        api_key=cast(Any, settings.api_key),
        base_url=settings.base_url,
    )
    lang_name = "Chinese" if lang == "zh" else "English"
    _LANG_HINT = "中文" if lang == "zh" else "English"

    # 分片发送，每片不超过 40 个函数（控制 token）
    chunk_size = 40
    for chunk_start in range(0, len(need_llm), chunk_size):
        chunk = need_llm[chunk_start : chunk_start + chunk_size]
        batch_lines: list[str] = []
        for idx, r in chunk:
            # 清洗源代码：去掉空行缩进，限制长度
            src_lines = r["source"].split("\n")
            # 只保留函数体（去掉装饰器行如果太长）
            src_clean = "\n".join(
                ln.rstrip()
                for ln in src_lines
                if ln.strip() and not ln.strip().startswith("@")
            )
            if len(src_clean) > 600:
                src_clean = src_clean[:600] + "..."
            orig = r["description"] or "(no description)"
            batch_lines.append(f"<{idx}>")
            batch_lines.append(f"CODE:\n{src_clean}")
            batch_lines.append(f"ORIG_DESC: {orig}")
            batch_lines.append(f"</{idx}>")

        prompt = (
            f"You are analyzing Python pytest test functions. For each one, read its "
            f"source code and any existing description, then write a concise "
            f"{_LANG_HINT} description (one short sentence, 10-25 words).\n"
            f"\n"
            f"Rules:\n"
            f"- Understand what the test DOES from the code (assertions, setups, calls).\n"
            f"- The function name uses snake_case; use code context to infer meaning.\n"
            f"- Keep technical terms (HTTP status codes, API names, data types) verbatim.\n"
            f"- If ORIG_DESC already describes it clearly in {_LANG_HINT}, keep it as-is.\n"
            f"- Do NOT add numbering, bullets, or extra commentary.\n"
            f"- Return exactly one line per test, in the format: <INDEX> <description>\n"
            f"\n"
            f"Examples (for English output):\n"
            f'  <0> CODE:\\ndef test_construct_with_unknown():\\n    exc = YelpError("msg", "unknown")\\n\\nORIG_DESC: (no description)\n'
            f"  <0> Constructs YelpError with unknown error type\n"
            f'  <1> CODE:\\ndef test_login_success():\\n    result = auth.login("user", "pass")\\n    assert result.token\n'
            f"  <1> Login with correct credentials returns a token\n"
            f"\n"
            f"Now process the following:\n" + "\n".join(batch_lines)
        )

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a concise {lang_name} technical writer for test documentation.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                timeout=120,
                max_tokens=4096,
            )
            content = resp.choices[0].message.content or ""
            for line in content.strip().split("\n"):
                m = re.match(r"^<(\d+)>\s*(.*)", line.strip())
                if m:
                    idx = int(m.group(1))
                    desc = m.group(2).strip()
                    if desc:
                        # 找到对应的 row 并更新
                        for ri, rr in chunk:
                            if ri == idx:
                                rr["description"] = desc
                                break
        except Exception as e:
            print(
                f"[WARN] LLM enrichment failed for chunk {chunk_start}: {e}",
                file=sys.stderr,
            )


# ── Markdown 生成 ──────────────────────────────────────────────────────────

MODULE_LABELS: dict[str, str] = {
    "路由": "Routing",
    "服务": "Service",
    "数据": "Data",
    "Schema": "Schema",
    "模型": "Model",
    "LLM": "LLM",
    "RAG": "RAG",
    "核心": "Core",
    "工具": "Utility",
}

TYPE_LABELS_ZH: dict[str, str] = {
    "纯单元": "纯单元",
    "Mock服务": "Mock服务",
    "Mock外部API": "Mock外部API",
    "集成": "集成",
}

TYPE_LABELS_EN: dict[str, str] = {
    "纯单元": "Unit",
    "Mock服务": "Mocked Service",
    "Mock外部API": "Mocked API",
    "集成": "Integration",
}

COL_HEADERS_ZH = ["类", "函数", "描述", "标记", "类型"]
COL_HEADERS_EN = ["Class", "Function", "Description", "Markers", "Type"]


def generate_markdown(
    rows: list[dict],
    lang: str,
    *,
    no_translate: bool = False,
) -> str:
    """生成 Markdown 测试用例文档。"""
    headers = COL_HEADERS_EN if lang == "en" else COL_HEADERS_ZH
    type_labels = TYPE_LABELS_EN if lang == "en" else TYPE_LABELS_ZH

    # ── LLM 描述增强 ──
    has_api = bool(settings.api_key or os.environ.get("API_KEY"))
    if has_api and not no_translate:
        _batch_enrich(
            rows,
            lang,
            api_key=settings.api_key or os.environ.get("API_KEY", ""),
            base_url=settings.base_url,
        )
    elif lang == "en" and not has_api:
        print(
            "[WARN] --lang en 但未找到 API_KEY，跳过 LLM 增强（仅保留原始描述）",
            file=sys.stderr,
        )

    # ── 分模块统计 ──
    module_counts: dict[str, int] = {}
    for r in rows:
        module_counts[r["module"]] = module_counts.get(r["module"], 0) + 1

    # ── 构建文档 ──
    lines: list[str] = []
    title = "测试用例文档" if lang == "zh" else "Test Case Documentation"
    lines.append(f"# {title}")
    lines.append("")
    lines.append(
        "> 自动生成，请勿手动编辑。重新生成：`python generate_test_docs.py --lang <zh|en>`"
        if lang == "zh"
        else "> Auto-generated. Do not edit manually. Regenerate with: `python generate_test_docs.py --lang <zh|en>`"
    )
    lines.append("")

    # ── 汇总表 ──
    lines.append("## " + ("概览" if lang == "zh" else "Overview"))
    lines.append("")
    lines.append(
        f"| {'模块' if lang == 'zh' else 'Module'} | {'数量' if lang == 'zh' else 'Count'} |"
    )
    lines.append("|---|---|")
    for mod in sorted(module_counts, key=lambda m: -module_counts[m]):
        label = MODULE_LABELS.get(mod, mod) if lang == "en" else mod
        lines.append(f"| {label} | {module_counts[mod]} |")
    lines.append(f"| **{'合计' if lang == 'zh' else 'Total'}** | **{len(rows)}** |")
    lines.append("")

    # ── 分组输出 ──
    current_module = None
    current_file = None
    for r in rows:
        mod_label = (
            MODULE_LABELS.get(r["module"], r["module"]) if lang == "en" else r["module"]
        )
        file_label = r["file"].replace(".py", "")

        if r["module"] != current_module:
            current_module = r["module"]
            current_file = None
            lines.append("---\n")
            lines.append(f"## {mod_label}")
            lines.append("")

        if r["file"] != current_file:
            current_file = r["file"]
            lines.append("")  # 与上节隔开
            lines.append(f"### {file_label}")
            lines.append("")
            lines.append(f"| {' | '.join(headers)} |")
            lines.append(f"|{'|'.join(':---:' for _ in headers)}|")

        desc = r["description"]
        # 如果是空描述，显示函数名（斜体标识）
        if not desc:
            desc = f"*{r['func']}*"

        cells = [
            r["class"],
            r["func"].replace("test_", ""),
            desc,
            r["markers"],
            type_labels.get(r["type"], r["type"]),
        ]
        lines.append(f"| {' | '.join(cells)} |")

    lines.append("")
    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="生成测试用例文档")
    parser.add_argument(
        "--lang", choices=["zh", "en"], default="zh", help="输出语言（默认 zh）"
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="输出路径")
    parser.add_argument(
        "-n",
        "--no-translate",
        action="store_true",
        help="跳过 LLM 调用（仅清洗/翻译已有文本）",
    )
    args = parser.parse_args()

    print(f"[INFO] 解析测试文件: {TEST_DIR}")
    rows = _walk_tests()
    print(f"[INFO] 共发现 {len(rows)} 个测试函数")

    md = generate_markdown(rows, args.lang, no_translate=args.no_translate)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    print(f"[INFO] 文档已写入: {output_path}")

    if (
        args.lang == "en"
        and not args.no_translate
        and not (settings.api_key or os.environ.get("API_KEY"))
    ):
        print(
            "[WARN] 未找到 API_KEY，英文描述未使用 LLM 增强（仅保留原始描述）",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
