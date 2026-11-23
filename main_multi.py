"""Unified multi-brand entry point — one EXE, every brand selectable.

With flags -> CLI mode with a mandatory --brand NAME (or the default brand
listed in BrandConfig). Without flags -> GUI with a brand picker at the top.

    python main_multi.py                       # GUI, brand picker
    python main_multi.py --brand baidu --scan-only
    python main_multi.py --list-engines
"""

import sys
import os

# Ensure antivancedcore is importable when running from source (no install).
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import antivancedcore.app as _app
from antivancedcore.brand import load_all_brands


def _default_cfg():
    """The first brand becomes the default target for picker + footer."""
    registry = load_all_brands()
    return registry["baidu"], registry


def main() -> int:
    cfg, registry = _default_cfg()

    # CLI mode: an explicit flag is present.
    if len(sys.argv) > 1:
        # --brand selects which CFG to run against.
        argv = list(sys.argv[1:])
        import argparse

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--brand", default=None)
        known, unknown = parser.parse_known_args(argv)
        cli_args = unknown  # everything except --brand

        if known.brand:
            key = known.brand.lower()
            if key not in registry:
                print(f"unknown brand: {known.brand}")
                print(f"known: {', '.join(sorted(registry))}")
                return 1
            cfg = registry[key]

        import antivancedcore.cli as cli

        edition = "extended" if "extended" in cli_args else "vanced"
        return cli.main(cfg, cli_args, profile=edition)

    # GUI mode with a brand picker across all 10 brands.
    _app.run(cfg, "vanced", brands=registry)
    return 0


if __name__ == "__main__":
    sys.exit(main())
