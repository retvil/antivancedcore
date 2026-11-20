"""AntiVKGroupVanced entry point (EXTENDED edition).

With flags -> CLI mode; without -> GUI.
All behaviour is driven by brands/mailru/brand_config.py (anti-vanced-core).
"""

import sys

import antivancedcore
from antivancedcore import app, cli
from brands.mailru.brand_config import CFG

if __name__ == "__main__" and len(sys.argv) > 1:
    sys.exit(cli.main(CFG, sys.argv[1:]))

app.run(CFG, "extended")
