"""User exclusions for scan findings, persisted across sessions.

Excluded findings are deselected by default in future scans, but the user
can still pick them in the selection dialog. The persistence location is
driven by ``BrandConfig.base_dir`` so this module is shared by every brand.
"""

import json
from pathlib import Path

from antivancedcore.brand import BrandConfig


def _file(cfg: BrandConfig) -> Path:
    return cfg.base_dir / "exclusions.json"


def load(cfg: BrandConfig) -> set[str]:
    """Load the exclusion set; empty set on missing or corrupt file."""
    try:
        data = json.loads(_file(cfg).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    if not isinstance(data, list):
        return set()
    return {item for item in data if isinstance(item, str)}


def save(cfg: BrandConfig, items: set[str]) -> None:
    """Persist the exclusion set (best effort, never raises)."""
    try:
        cfg.base_dir.mkdir(parents=True, exist_ok=True)
        _file(cfg).write_text(
            json.dumps(sorted(items), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def is_excluded(cfg: BrandConfig, finding: str, items: set[str] | None = None) -> bool:
    """True if the finding is in the exclusion set."""
    if items is None:
        items = load(cfg)
    return finding in items


def add(cfg: BrandConfig, finding: str) -> None:
    """Add one finding to the exclusion set."""
    items = load(cfg)
    items.add(finding)
    save(cfg, items)


def clear(cfg: BrandConfig) -> None:
    """Remove all exclusions."""
    save(cfg, set())
