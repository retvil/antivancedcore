"""Verify every finding prefix a scanner emits has a handler in _remove_one.

Handles both forms of dispatch:
    if finding.startswith("Prefix: "):
    if finding.startswith(("A: ", "B: ", "C: ")):

A recall engine that can detect but not remove a vector is broken, so this is a
real completeness check, not a lint.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BRANDS = ["baidu", "sogou", "ant2345", "ucweb", "naver",
          "kakao", "qq", "wechat", "tencent", "mailru"]

# User-data vectors are consent-gated and cleaned through the browser-profile
# path rather than a per-finding prefix handler.
INFO_ONLY = {
    "Browser extension", "Extension", "Cookie", "Cookies", "History",
}

# Strings that look like findings in source but are not.
NOT_FINDINGS = {"remove_selected", "Error", "Warning", "Note", "Value", "Name",
                "Key", "Data", "Type", "Path", "Status", "Result"}


def _body(src: str, fn: str) -> str:
    m = re.search(rf"def {fn}\(.*?\n(?=\ndef |\nclass |\Z)", src, re.S)
    return m.group(0) if m else ""


def emitted(src: str) -> set[str]:
    body = _body(src, "scan_all")
    # Findings are produced by the individual scan_* functions, not scan_all,
    # so scan the whole module but skip the removal half.
    cut = src.find("def _remove_one")
    scan_src = src[:cut] if cut > 0 else src
    out = set()
    for m in re.finditer(r"""f["']([A-Za-z][A-Za-z0-9 _\-]{1,45}?): \{""", scan_src):
        out.add(m.group(1).strip())
    return out


def handled(src: str) -> set[str]:
    body = _body(src, "_remove_one")
    out = set()
    # single: startswith("X: ")
    for m in re.finditer(r"""startswith\((?:f)?["']([A-Za-z][A-Za-z0-9 _\-]{1,45}?): """, body):
        out.add(m.group(1).strip())
    # tuple: startswith(("A: ", "B: ", ...))
    for m in re.finditer(r"""startswith\(\s*\((.*?)\)\s*\)""", body, re.S):
        for mm in re.finditer(r"""["']([A-Za-z][A-Za-z0-9 _\-]{1,45}?): """, m.group(1)):
            out.add(mm.group(1).strip())
    return out


def main() -> int:
    problems = []
    for brand in BRANDS:
        src = (ROOT / "brands" / brand / f"{brand}_detect.py").read_text(encoding="utf-8")
        miss = sorted(
            p for p in emitted(src) - handled(src)
            if p not in INFO_ONLY and p not in NOT_FINDINGS
        )
        if miss:
            problems.append(f"{brand}: {miss}")

    if problems:
        print("EMITTED BUT NOT REMOVABLE:")
        for p in problems:
            print("  " + p)
        return 1

    print("every emitted finding prefix has a removal handler")
    return 0


if __name__ == "__main__":
    sys.exit(main())
