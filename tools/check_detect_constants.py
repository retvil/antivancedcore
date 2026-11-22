"""Check that every CONSTANT referenced via `det.X` in core exists in all brands."""

import importlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BRANDS = ["baidu", "sogou", "ant2345", "ucweb", "naver",
          "kakao", "qq", "wechat", "tencent", "mailru"]

src = ""
for name in ("app.py", "cli.py"):
    src += (ROOT / "antivancedcore" / name).read_text(encoding="utf-8")

attrs = sorted(set(re.findall(r"\bdet\.([A-Z][A-Z0-9_]*)", src)))
print("det.CONST accesses:", attrs)

problems = []
for attr in attrs:
    for b in BRANDS:
        det = importlib.import_module(f"brands.{b}.{b}_detect")
        if not hasattr(det, attr):
            problems.append(f"{b}: missing {attr}")

print("\n".join(problems) if problems else "all constants present in all brands")
sys.exit(1 if problems else 0)
