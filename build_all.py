"""Build one-file EXE for every brand in the monorepo.

Usage:
    python build_all.py                 # all 10 brands, VANCED edition
    python build_all.py baidu mailru    # only these brands
    python build_all.py --extended      # EXTENDED edition entry points
    python build_all.py --clean         # wipe build/ and dist/ first

Output: dist/<brand>-vanced.exe (or <brand>-extended.exe).

PyInstaller needs the core package and the brand package as hidden imports so
that the frozen app can resolve them at runtime (they're imported dynamically
via BrandConfig.load_detect_module()).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

BRANDS = [
    "baidu", "sogou", "ant2345", "ucweb", "naver",
    "kakao", "qq", "wechat", "tencent", "mailru",
]

CORE_MODULES = [
    "antivancedcore",
    "antivancedcore.brand",
    "antivancedcore.backup",
    "antivancedcore.products_detect",
    "antivancedcore.profiles",
    "antivancedcore.policies",
    "antivancedcore.engines",
    "antivancedcore.exclusions",
    "antivancedcore.report",
    "antivancedcore.restore",
    "antivancedcore.translations",
    "antivancedcore.updater",
    "antivancedcore.watchdog",
    "antivancedcore.cli",
    "antivancedcore.app",
]

THIRD_PARTY = ["tkinter", "ttkbootstrap", "psutil"]


def build(brand: str, extended: bool) -> bool:
    edition = "extended" if extended else "vanced"
    entry = ROOT / "brands" / brand / f"main{'_extended' if extended else ''}.py"
    if not entry.is_file():
        print(f"[{brand}] missing entry point: {entry}")
        return False

    name = f"{brand}-{edition}"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed", f"--name={name}",
        "--noconfirm",
    ]
    for mod in CORE_MODULES + THIRD_PARTY:
        cmd.append(f"--hidden-import={mod}")
    cmd += [
        f"--hidden-import=brands.{brand}",
        f"--hidden-import=brands.{brand}.{brand}_detect",
        str(entry),
    ]

    print(f"[{brand}] building {name}.exe ...")
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[{brand}] FAILED")
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        return False

    exe = ROOT / "dist" / f"{name}.exe"
    size = exe.stat().st_size if exe.is_file() else 0
    print(f"[{brand}] OK  {exe.name}  {size:,} bytes")
    return exe.is_file()


def build_multi() -> bool:
    """One EXE that bundles all 10 brands with a runtime picker."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed", "--name=antivancedcore",
        "--noconfirm",
    ]
    for mod in CORE_MODULES + THIRD_PARTY:
        cmd.append(f"--hidden-import={mod}")
    for brand in BRANDS:
        cmd += [
            f"--hidden-import=brands.{brand}",
            f"--hidden-import=brands.{brand}.{brand}_detect",
            f"--hidden-import=brands.{brand}.brand_config",
        ]
    cmd += ["main_multi.py"]

    print("[multi] building antivancedcore.exe (all 10 brands) ...")
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print("[multi] FAILED")
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        return False

    exe = ROOT / "dist" / "antivancedcore.exe"
    size = exe.stat().st_size if exe.is_file() else 0
    print(f"[multi] OK  {exe.name}  {size:,} bytes")
    return exe.is_file()


def main(argv: list[str]) -> int:
    extended = "--extended" in argv
    clean = "--clean" in argv
    multi = "--multi" in argv
    picked = [a for a in argv if not a.startswith("--")] or BRANDS

    unknown = [b for b in picked if b not in BRANDS]
    if unknown:
        print(f"unknown brand(s): {', '.join(unknown)}")
        print(f"known: {', '.join(BRANDS)}")
        return 2

    if clean:
        for d in ("build", "dist"):
            shutil.rmtree(ROOT / d, ignore_errors=True)
        print("cleaned build/ and dist/")

    if multi:
        ok = build_multi()
        print()
        print("multi EXE: " + ("OK" if ok else "FAILED"))
        return 0 if ok else 1

    built = [b for b in picked if build(b, extended)]
    failed = [b for b in picked if b not in built]

    print()
    print(f"built {len(built)}/{len(picked)}")
    if failed:
        print(f"failed: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
