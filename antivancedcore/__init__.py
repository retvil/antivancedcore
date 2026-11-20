"""AntiVancedCore — brand-agnostic core for the Anti<Brand>Vanced family.

Import surface::

    from antivancedcore import BrandConfig, run, scan, apply_policy, ...

Each brand supplies a ``BrandConfig`` (``brands/<name>/brand_config.py``); the
core modules below are driven entirely by that object. The only brand-specific
code that stays out of the core is the ``<brand>_detect`` module (the scan /
removal engine), referenced by name via ``BrandConfig.detect_module``.
"""

from antivancedcore.brand import BrandConfig

__all__ = [
    "BrandConfig",
    "engines",
    "policies",
    "backup",
    "exclusions",
    "restore",
    "updater",
    "watchdog",
    "report",
    "cli",
    "app",
]

__version__ = "1.4.0"
