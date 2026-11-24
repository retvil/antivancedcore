"""Regression: run() must declare every variable update_ui() touches as global.

update_ui() runs inside run() and touches root, status_label, findings_box,
main_label, the button widgets, and footer_label. If any of these is only a
local in run(), update_ui() raises NameError at launch (exactly what the
multi-brand picker exposed). This test parses app.py and fails if a name that
update_ui() references is not declared global by run().
"""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _global_names(fn: str) -> set[str]:
    """Names declared global inside the function ``fn`` of app.py."""
    tree = ast.parse(
        (Path(__file__).resolve().parents[1] / "antivancedcore" / "app.py").read_text(encoding="utf-8")
    )
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == fn:
            names = set()
            for sub in node.body:
                if isinstance(sub, ast.Global):
                    names.update(sub.names)
            return names
    return set()


def test_update_ui_references_are_global_in_run():
    """update_ui() is nested in run(); every name it configures must be a
    global of run() so the nested function's closure sees the same objects."""
    tree = ast.parse(
        (Path(__file__).resolve().parents[1] / "antivancedcore" / "app.py").read_text(encoding="utf-8")
    )

    run_fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run")
    run_globals = set()
    for sub in run_fn.body:
        if isinstance(sub, ast.Global):
            run_globals.update(sub.names)

    # Names update_ui() configures via .configure() on widget attributes.
    ui_refs = set()
    update_ui = next(n for n in run_fn.body if isinstance(n, ast.FunctionDef) and n.name == "update_ui")
    for node in ast.walk(update_ui):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            ui_refs.add(node.value.id)
    # Also the names used inside f-strings / text= calls of those widgets.

    # Every widget update_ui touches must be a global of run().
    missing = ui_refs - run_globals - {
        "t", "update_status", "_render_findings", "STATUS_COLORS",
    }
    assert not missing, (
        "update_ui() references these names that run() did not declare global: "
        f"{sorted(missing)}"
    )
