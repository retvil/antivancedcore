"""Verify a built dist/ folder: GUI launch + CLI for every brand EXE.

Usage:
    python verify_build.py                 # GUI + CLI + scan for dist/*.exe
    python verify_build.py --skip-gui      # CLI only (faster, headless)

Checks per binary:
  1. gui  - launch and confirm the process is still alive after 8 seconds.
  2. cli  - `--list-engines` exits 0.
  3. scan - `--scan-only --profile vanced` exits 0 (clean) or 2 (findings found).

Exit code 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

GUI_ALIVE_SECONDS = 8


def _kill_tree(proc: subprocess.Popen) -> None:
    """Kill the PyInstaller bootloader and the child process it spawned."""
    subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
        capture_output=True,
    )


def check_gui(exe: Path) -> tuple[bool, str]:
    proc = subprocess.Popen([str(exe)])
    try:
        time.sleep(GUI_ALIVE_SECONDS)
        if proc.poll() is None:
            return True, f"alive after {GUI_ALIVE_SECONDS}s"
        return False, f"exited early (code {proc.returncode})"
    finally:
        if proc.poll() is None:
            _kill_tree(proc)


def check_cli(exe: Path, args: list[str], ok_codes: set[int]) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            [str(exe), *args],
            capture_output=True,
            text=True,
            timeout=900,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout"

    ok = proc.returncode in ok_codes
    detail = f"exit={proc.returncode}"
    if not ok:
        output = (proc.stderr or proc.stdout or "").strip().splitlines()
        detail += " | " + " / ".join(output[-3:]) if output else ""
    return ok, detail


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="dist", help="folder holding the EXEs")
    ap.add_argument("--skip-gui", action="store_true",
                    help="skip the GUI launch check")
    args = ap.parse_args(argv)

    exes = sorted(Path(args.dir).glob("*.exe"))
    if not exes:
        print(f"no EXE found in {args.dir}")
        return 1

    rows: list[tuple[str, str, bool, str]] = []
    for exe in exes:
        if not args.skip_gui:
            ok, detail = check_gui(exe)
            rows.append((exe.name, "gui", ok, detail))

        ok, detail = check_cli(exe, ["--list-engines"], {0})
        rows.append((exe.name, "cli", ok, detail))

        ok, detail = check_cli(exe, ["--scan-only", "--profile", "vanced"], {0, 2})
        rows.append((exe.name, "scan", ok, detail))

    width = max(len(r[0]) for r in rows)
    for name, kind, ok, detail in rows:
        print(f"{name:<{width}}  {kind:4s}  {'PASS' if ok else 'FAIL'}  {detail}")

    failed = [r for r in rows if not r[2]]
    print()
    print(f"{len(rows) - len(failed)}/{len(rows)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
