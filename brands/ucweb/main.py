"""
Auto-generated Anti<Brand>Vanced entry point.
Brand-specific values come from brand_config.py; behaviour from antivancedcore.
"""

import sys
import os

# Ensure antivancedcore is importable when running from source (no install).
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import antivancedcore.app as _app
from brands.ucweb.brand_config import CFG

if __name__ == "__main__" and len(sys.argv) > 1:
    import antivancedcore.cli as cli
    sys.exit(cli.main(CFG, sys.argv[1:]))

_app.run(CFG, "vanced")
