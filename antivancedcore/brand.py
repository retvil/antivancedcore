"""AntiVancedCore — single source of truth for the Anti<Brand>Vanced family.

A thin layer of brand-agnostic core modules + one per-brand ``BrandConfig``.
Each brand (baidu, sogou, …, mailru) ships a ``brand_config.py`` that builds a
``BrandConfig``; the core modules read every brand-specific value from it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class BrandConfig:
    """All brand-specific constants for one Anti<Brand>Vanced product.

    Every brand-agnostic core module reads its values from this object instead
    of hard-coding a brand. The 10 brands each provide their own ``BrandConfig``
    (see ``brands/<name>/brand_config.py``).
    """

    # --- identity ---------------------------------------------------------
    name: str                       # "Baidu", "Sogou", "VK Group", ...
    detect_module: str              # importable brand-core module, e.g. "baidu_detect"
    repo: str                      # GitHub repo, e.g. "retvil/AntiBaiduVanced"
    appdata_dir: str               # %APPDATA%\<dir>, e.g. "AntiBaiduVanced"

    # --- release / build --------------------------------------------------
    product_names: dict            # {"vanced": "AntiBaiduVanced", "extended": "AntiBaiduExtended"}
    app_version: str = "1.4.0"
    app_author: str = "Nod33Eset"

    # --- removal scope ----------------------------------------------------
    kill_names: tuple = field(default_factory=tuple)       # browser/product EXE names
    browser_process_marker: str = ""                        # marker for exe-based kill
    consent_prefixes: tuple = field(default_factory=tuple) # findings that touch user data

    # --- policy enforcement ----------------------------------------------
    policy_vendor_key: str = ""      # e.g. r"SOFTWARE\Policies\Baidu\BaiduBrowser"
    policy_domain: str = ""          # e.g. "baidu.com" (matched in policy values)
    remove_func_name: str = ""       # e.g. "remove_baidu_search_policies"

    # --- watchdog ----------------------------------------------------------
    task_name: str = ""              # e.g. r"\AntiBaidu\PolicyWatch"

    # --- extended-edition scans ------------------------------------------
    product_markers: tuple = field(default_factory=tuple)   # e.g. ("baidu", "baidubrowser.exe")
    appx_match_pattern: str = ""      # e.g. "baidu|百度|baidubrowser|baidu\\.com"
    dns_ips: frozenset = field(default_factory=frozenset)  # brand's own DNS servers
    browser_dir_name: str = ""        # e.g. "baidubrowser" (excluded product-dir name)

    # --- i18n (brand-specific consent text, keyed by language code) -------
    consent_text: dict = field(default_factory=dict)

    # --- paths -------------------------------------------------------------
    @property
    def base_dir(self) -> Path:
        """%APPDATA%\<appdata_dir> — shared by backup/exclusions/restore/watchdog."""
        return Path(os.environ.get("APPDATA", "")) / self.appdata_dir

    @property
    def log_file(self) -> Path:
        """Operation log: <base_dir>/<name lower>.log."""
        return self.base_dir / f"anti{self.name.lower()}.log"

    @property
    def brand_dir(self) -> str:
        """Directory name under ``brands/`` (detect module minus ``_detect``)."""
        return self.detect_module.removesuffix("_detect")

    def load_detect_module(self):
        """Import and return this brand's detect (scan/remove) module.

        Resolution order:
          1. ``<detect_module>`` as a top-level module (flat per-brand fork).
          2. ``brands.<brand_dir>.<detect_module>`` (monorepo / frozen EXE).
        """
        import importlib

        try:
            return importlib.import_module(self.detect_module)
        except ModuleNotFoundError:
            return importlib.import_module(
                f"brands.{self.brand_dir}.{self.detect_module}"
            )

    def __str__(self) -> str:  # pragma: no cover - diagnostics
        return f"BrandConfig({self.name}, {self.repo}, {self.appdata_dir})"


__all__ = ["BrandConfig"]
