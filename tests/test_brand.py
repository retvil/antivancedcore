"""Validate every brand's BrandConfig and detect-module wiring.

For each brand under brands/ this test:
- imports its CFG (BrandConfig) and checks required fields are populated.
- imports its detect module and asserts the entry-point functions exist.
- checks the brand's appdata_dir / repo / task_name are non-empty.

This is the single-source-of-truth check: a new brand is complete when this
test passes for it.
"""

import importlib
import sys
from pathlib import Path

# Make the monorepo root importable regardless of where pytest is launched.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BRANDS = [
    "baidu", "sogou", "ant2345", "ucweb", "naver",
    "kakao", "qq", "wechat", "tencent", "mailru",
]

# Fields that must be non-empty on every BrandConfig.
REQUIRED_FIELDS = (
    "name", "detect_module", "repo", "appdata_dir",
    "kill_names", "task_name", "policy_vendor_key", "policy_domain",
    "product_markers", "browser_dir_name", "product_names",
)


def _load_cfg(brand: str):
    mod = importlib.import_module(f"brands.{brand}.brand_config")
    return mod.CFG


def _load_detect(brand: str):
    cfg = _load_cfg(brand)
    # The detect module is discoverable via the brand package
    det = importlib.import_module(f"brands.{brand}.{cfg.detect_module}")
    return det


def test_brand_configs_populated():
    for brand in BRANDS:
        cfg = _load_cfg(brand)
        for field in REQUIRED_FIELDS:
            val = getattr(cfg, field, None)
            assert val not in (None, "", (), {}), (
                f"{brand}: BrandConfig.{field} is empty"
            )
        # product_names must have both editions
        assert "vanced" in cfg.product_names and "extended" in cfg.product_names, (
            f"{brand}: product_names missing vanced/extended"
        )
        # base_dir is a Path under APPDATA
        assert str(cfg.base_dir).endswith(cfg.appdata_dir), (
            f"{brand}: base_dir does not end with appdata_dir"
        )


def test_brand_detect_modules_importable():
    for brand in BRANDS:
        det = _load_detect(brand)
        # The scan/remove entry points must exist on every detect module.
        for fn in ("scan_all", "remove_selected", "scan_uninstall_entries"):
            assert hasattr(det, fn), f"{brand}: detect module missing {fn}"
        # consent-gated finding markers
        assert hasattr(det, "CONSENT_PREFIXES"), f"{brand}: CONSENT_PREFIXES missing"


def test_brand_entry_points_exist():
    for brand in BRANDS:
        d = Path(__file__).resolve().parents[1] / "brands" / brand
        for entry in ("main.py", "main_extended.py", "brand_config.py"):
            assert (d / entry).is_file(), f"{brand}: missing {entry}"
