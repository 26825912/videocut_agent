"""扫描项目中所有相对导入，检查目标模块/符号是否存在。一次性诊断脚本。"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def module_paths(base_pkg: str, name: str | None):
    """base_pkg 是点号分隔的包名(基于 ROOT)，返回该包在文件系统的目录。"""
    parts = base_pkg.split(".") if base_pkg else []
    pkg_dir = os.path.join(ROOT, *parts)
    return pkg_dir


def resolve_and_check(file_path: str, level: int, module: str | None, names: list[str]):
    """file_path 触发了一个相对导入(level 个点)，检查 module 是否存在。"""
    # 计算 file 所在包
    rel = os.path.relpath(file_path, ROOT).replace("\\", "/")
    pkg_parts = rel.split("/")[:-1]  # 去掉文件名
    # 当前包 = 目录路径对应的包
    # level=1 表示当前包，level=2 上一级...
    up = level - 1
    if up > len(pkg_parts):
        return None  # 越界，忽略(可能是顶层脚本误用)
    base_parts = pkg_parts[: len(pkg_parts) - up] if up else pkg_parts[:]
    base_pkg_dir = os.path.join(ROOT, *base_parts)

    target_module = module  # from .X import ... 中的 X（可能是点号分隔，如 tools.image_search_tools）
    if target_module:
        sub_path = target_module.replace(".", os.sep)
        cand_py = os.path.join(base_pkg_dir, sub_path + ".py")
        cand_pkg = os.path.join(base_pkg_dir, sub_path, "__init__.py")
        cand_pkg_dir = os.path.join(base_pkg_dir, sub_path)
        if os.path.exists(cand_py) or os.path.exists(cand_pkg) or os.path.isdir(cand_pkg_dir):
            return None  # 模块存在
        return f"模块缺失: from {'.'*level}{target_module} import ... (查找: {os.path.relpath(cand_py, ROOT)})"
    else:
        # from . import a, b  -> 检查 base_pkg_dir/a.py 等每个 name
        missing = []
        for n in names:
            cand_py = os.path.join(base_pkg_dir, n + ".py")
            cand_pkg = os.path.join(base_pkg_dir, n, "__init__.py")
            cand_pkg_dir = os.path.join(base_pkg_dir, n)
            if not (os.path.exists(cand_py) or os.path.exists(cand_pkg) or os.path.isdir(cand_pkg_dir)):
                missing.append(n)
        if missing:
            return f"可能缺失: from {'.'*level} import {missing} (解析目录: {os.path.relpath(base_pkg_dir, ROOT)})"
        return None


def scan():
    problems = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # 跳过缓存、前端、虚拟环境
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".web", "node_modules", ".git", "data")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=fp)
            except Exception as e:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level and node.level > 0:
                    names = [a.name for a in node.names]
                    res = resolve_and_check(fp, node.level, node.module, names)
                    if res:
                        problems.append((os.path.relpath(fp, ROOT), node.lineno, res))
    return problems


if __name__ == "__main__":
    probs = scan()
    # 排除扫描脚本自身
    probs = [p for p in probs if "_scan_imports" not in p[0]]
    if not probs:
        print("OK 未发现相对导入缺失模块")
    else:
        print(f"发现 {len(probs)} 处可能的导入问题:")
        for f, line, msg in probs:
            print(f"  {f}:{line}  {msg}")
