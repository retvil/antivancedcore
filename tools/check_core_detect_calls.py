"""Cross-check every core -> detect-module call against the real signatures.

The 10-brand refactor left several call sites passing the wrong number of
arguments (scan_all(profile, cfg) vs scan_all(profile); remove_selected(x, CFG)
vs remove_selected(x)). This script finds them all at once by binding the actual
arguments symbolically.

Usage: python check_core_detect_calls.py
"""

from __future__ import annotations

import ast
import importlib
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BRANDS = ["baidu", "sogou", "ant2345", "ucweb", "naver",
          "kakao", "qq", "wechat", "tencent", "mailru"]


def calls_in(module_file: Path) -> list[tuple[int, str, str, int]]:
    """Return (lineno, receiver, attr, n_args) for receiver.attr(...) calls."""
    tree = ast.parse(module_file.read_text(encoding="utf-8"))
    out = []

    # collect aliases: "det = _detect()" -> {"det"}
    aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            fn = node.value.func
            name = getattr(fn, "id", None) or getattr(fn, "attr", None)
            if name in ("_detect", "_detect_module"):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        aliases.add(t.id)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        recv = node.func.value
        recv_name = getattr(recv, "id", None)
        if isinstance(recv, ast.Call):
            inner = getattr(recv.func, "id", None) or getattr(recv.func, "attr", None)
            recv_name = "_detect" if inner in ("_detect", "_detect_module") else None
        if recv_name in aliases or recv_name in ("_detect", "_detect_module"):
            out.append((node.lineno, recv_name, node.func.attr, len(node.args)))
    return out


def main() -> int:
    cfg = importlib.import_module("brands.baidu.brand_config").CFG
    det = cfg.load_detect_module()
    core = ROOT / "antivancedcore"

    problems = []
    for f in sorted(core.glob("*.py")):
        for lineno, recv, attr, n_args in calls_in(f):
            fn = getattr(det, attr, None)
            if fn is None:
                problems.append(f"{f.name}:{lineno}: detect has no attribute {attr}")
                continue
            try:
                sig = inspect.signature(fn)
            except (TypeError, ValueError):
                continue
            params = [
                p for p in sig.parameters.values()
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            ]
            required = [p for p in params if p.default is p.empty]
            if n_args < len(required) or n_args > len(params):
                problems.append(
                    f"{f.name}:{lineno}: {attr}() called with {n_args} args, "
                    f"signature {sig}"
                )

    if problems:
        print("MISMATCHES:")
        for p in problems:
            print("  " + p)
        return 1

    print("all core -> detect calls match their signatures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
