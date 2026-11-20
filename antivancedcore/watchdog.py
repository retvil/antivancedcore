"""Policy watchdog: a daily Windows scheduled task that re-applies the
default-search policy, so a re-hijack cannot survive until the next manual
run.

The task runs the installed EXE (or python main.py) with the
--apply-policy <engine> flag. The task name and state file are driven by
``BrandConfig`` so this module is shared by every brand. Install/remove are
best-effort; failures are reported, never fatal.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from antivancedcore.brand import BrandConfig


def _state_file(cfg: BrandConfig) -> Path:
    return cfg.base_dir / "watchdog.json"


def is_installed(cfg: BrandConfig) -> bool:
    try:
        proc = subprocess.run(
            ["schtasks", "/query", "/tn", cfg.task_name], capture_output=True, timeout=15
        )
        return proc.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _exe_path() -> str:
    """Prefer the frozen EXE so a daily task works without Python."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "main.py")


def install(cfg: BrandConfig, engine_name: str) -> str:
    """Create the daily task. Returns the task id."""
    sf = _state_file(cfg)
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(
        json.dumps({"engine": engine_name, "task": cfg.task_name}), encoding="utf-8"
    )
    exe = _exe_path()
    if exe.endswith(".py"):
        cmd = f'"{sys.executable}" "{exe}" --apply-policy {engine_name} --yes'
    else:
        cmd = f'"{exe}" --apply-policy {engine_name} --yes'
    args = [
        "schtasks", "/create", "/tn", cfg.task_name,
        "/tr", cmd,
        "/sc", "daily", "/st", "03:00",
        "/f",
    ]
    proc = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip()[:300])
    return cfg.task_name


def remove(cfg: BrandConfig) -> None:
    try:
        subprocess.run(
            ["schtasks", "/delete", "/tn", cfg.task_name, "/f"],
            capture_output=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        _state_file(cfg).unlink(missing_ok=True)
    except OSError:
        pass


def state(cfg: BrandConfig) -> dict | None:
    sf = _state_file(cfg)
    try:
        if sf.is_file():
            return json.loads(sf.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return None
