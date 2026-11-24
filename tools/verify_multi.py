"""Verify the multi-brand EXE: GUI launch + CLI routing to several brands."""

import subprocess
import sys
import time
from pathlib import Path

EXE = Path(r"D:\Project\AntiVancedCore\dist\antivancedcore.exe")
GUI_SECONDS = 10


def kill_tree(pid: int) -> None:
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)


def main() -> int:
    if not EXE.is_file():
        print(f"missing {EXE}")
        return 1

    # GUI: launch and confirm it stays alive (picker renders without crashing).
    proc = subprocess.Popen([str(EXE)])
    time.sleep(GUI_SECONDS)
    alive = proc.poll() is None
    if alive:
        kill_tree(proc.pid)
    print(f"gui  {'PASS' if alive else 'FAIL'}  "
          f"{'alive after ' + str(GUI_SECONDS) + 's' if alive else 'exited early'}")

    # CLI: route to a few different brands and accept exit 0/2.
    failed = 0
    for brand, args in [
        ("baidu", ["--brand", "baidu", "--scan-only", "--profile", "vanced"]),
        ("mailru", ["--brand", "mailru", "--scan-only", "--profile", "extended"]),
        ("qq", ["--brand", "qq", "--list-engines"]),
    ]:
        r = subprocess.run([str(EXE), *args], capture_output=True, text=True, timeout=900)
        ok = r.returncode in (0, 2)
        failed += 0 if ok else 1
        print(f"cli-{brand:6s} {'PASS' if ok else 'FAIL'}  exit={r.returncode}")

    # Unknown brand must fail cleanly.
    r = subprocess.run([str(EXE), "--brand", "bogus"], capture_output=True, text=True, timeout=60)
    ok = r.returncode == 1 and "unknown brand" in (r.stdout + r.stderr)
    failed += 0 if ok else 1
    print(f"cli-bogus  {'PASS' if ok else 'FAIL'}  exit={r.returncode}")

    total = 4 + 1
    print(f"\n{total - failed}/{total} multi checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
