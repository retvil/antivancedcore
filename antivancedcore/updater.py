"""Lightweight update check against the GitHub releases API.

No third-party deps: uses urllib. Best-effort — any failure (offline,
non-standard hosts, timeouts) returns None so the GUI can silently skip.
The target release URL is built from ``BrandConfig.repo``.
"""

import json
import re
import urllib.request

from antivancedcore.brand import BrandConfig


def _latest_release_url(cfg: BrandConfig) -> str:
    return f"https://api.github.com/repos/{cfg.repo}/releases/latest"


def fetch_latest_version(cfg: BrandConfig) -> str | None:
    """Return the latest release tag (e.g. 'v1.3.0') or None when offline."""
    try:
        req = urllib.request.Request(
            _latest_release_url(cfg),
            headers={
                "User-Agent": f"{cfg.name}Vanced/{cfg.app_version}",
                "Accept": "application/vnd.github+json",
            },
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        tag = (data.get("tag_name") or "").strip()
        return tag or None
    except (OSError, ValueError, TimeoutError):
        return None


def _parse(tag_or_version: str) -> tuple[int, int, int]:
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", tag_or_version)
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def is_newer(cfg: BrandConfig, latest_tag: str | None) -> bool:
    """True when ``latest_tag`` (e.g. 'v1.3.0') is greater than cfg.app_version."""
    if not latest_tag:
        return False
    return _parse(latest_tag) > _parse(cfg.app_version)
