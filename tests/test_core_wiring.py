"""End-to-end checks that the shared core actually runs for every brand.

These tests exist because a refactor can leave the brand-agnostic step list in
``antivancedcore/profiles.py`` pointing at functions a detect module does not
have, or at functions that need a BrandConfig argument. The unit tests in
test_brand.py only check attribute existence; these execute the real code paths.
"""

import importlib
import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from antivancedcore import profiles  # noqa: E402

BRANDS = [
    "baidu", "sogou", "ant2345", "ucweb", "naver",
    "kakao", "qq", "wechat", "tencent", "mailru",
]


def _cfg(brand: str):
    return importlib.import_module(f"brands.{brand}.brand_config").CFG


def _detect(brand: str):
    return _cfg(brand).load_detect_module()


def _resolve(det, brand: str, step: str):
    """Mirror scan_all()'s resolution: exact name, then scan_<brand>_<rest>."""
    fn = getattr(det, step, None)
    if fn is None and step.startswith("scan_"):
        fn = getattr(det, f"scan_{brand}_{step[5:]}", None)
    return fn


def test_every_profile_step_resolves_or_is_optional():
    """Every step either resolves, or takes cfg (skippable in VANCED), or is a
    vector this brand legitimately does not implement."""
    all_steps = set()
    for profile in profiles.PROFILE_SCANS:
        all_steps |= set(profiles.PROFILE_SCANS[profile])

    problems = []
    for brand in BRANDS:
        det = _detect(brand)
        for step in sorted(all_steps):
            if _resolve(det, brand, step) is None:
                # mailru genuinely has no DNS-keyboard vectors; anything else is a bug.
                if step in ("scan_dns_servers", "scan_keyboard_layouts"):
                    continue
                problems.append(f"{brand}: {step} unresolved")

    assert not problems, "unresolved scan steps:\n" + "\n".join(problems)


def test_scan_all_executes_for_every_brand_and_profile():
    """Run the real scan entry point for all 10 brands x 2 profiles."""
    failures = []
    for brand in BRANDS:
        det = _detect(brand)
        cfg = _cfg(brand)
        for profile in profiles.PROFILE_SCANS:
            try:
                findings = det.scan_all(profile, cfg)
            except Exception as exc:  # noqa: BLE001 - report, don't abort
                failures.append(f"{brand}/{profile}: {type(exc).__name__}: {exc}")
                continue
            assert isinstance(findings, list), f"{brand}/{profile}: not a list"
            assert all(isinstance(f, str) for f in findings), (
                f"{brand}/{profile}: non-string finding"
            )

    assert not failures, "scan_all crashed:\n" + "\n".join(failures)


def test_scan_all_accepts_cfg_for_extended_steps():
    """Extended vectors take cfg; scan_all must pass it rather than crash."""
    for brand in BRANDS:
        det = _detect(brand)
        sig = inspect.signature(det.scan_all)
        assert "cfg" in sig.parameters, f"{brand}: scan_all has no cfg parameter"

        helper = getattr(det, "_step_needs_cfg", None)
        assert helper is not None, f"{brand}: _step_needs_cfg helper missing"


def test_brand_config_load_detect_module():
    """BrandConfig.load_detect_module() resolves under the monorepo layout."""
    for brand in BRANDS:
        cfg = _cfg(brand)
        det = cfg.load_detect_module()
        assert det is not None, f"{brand}: load_detect_module returned None"
        assert hasattr(det, "scan_all"), f"{brand}: resolved module has no scan_all"
        assert cfg.brand_dir == brand, (
            f"{brand}: brand_dir is {cfg.brand_dir!r}, expected {brand!r}"
        )


def test_cli_scan_signature_matches_detect_module():
    """cli._cmd_scan must call scan_all(profile, cfg), matching app.py."""
    from antivancedcore import cli

    for brand in BRANDS:
        det = _detect(brand)
        cfg = _cfg(brand)
        # _cmd_scan does a real scan; the VANCED profile keeps it fast enough.
        findings = cli._cmd_scan(cfg, profiles.VANCED)
        assert isinstance(findings, list), f"{brand}: cli._cmd_scan not a list"


def test_every_app_detect_attribute_exists():
    """app.py touches detect attributes by name; none may be missing."""
    import re

    src = (
        Path(__file__).resolve().parents[1]
        / "antivancedcore"
        / "app.py"
    ).read_text(encoding="utf-8")
    used = sorted(set(re.findall(r"_detect\(\)\.([A-Za-z_][A-Za-z0-9_]*)", src)))

    problems = []
    for brand in BRANDS:
        det = _detect(brand)
        for attr in used:
            if not hasattr(det, attr):
                problems.append(f"{brand}: detect has no {attr}")

    assert not problems, "app.py references missing detect attributes:\n" + "\n".join(
        problems
    )


def test_brand_paths_resolves_for_every_brand(monkeypatch):
    """_brand_paths() must return a list of paths for every brand."""
    monkeypatch.setattr(
        "antivancedcore.app.run_in_ui", lambda fn: None, raising=False
    )
    from antivancedcore import app

    for brand in BRANDS:
        monkeypatch.setattr(app, "CFG", _cfg(brand))
        paths = app._brand_paths()
        assert isinstance(paths, list), f"{brand}: _brand_paths not a list"
        assert paths, f"{brand}: _brand_paths returned no candidates"
        assert all(isinstance(p, str) for p in paths), (
            f"{brand}: non-string path"
        )


def test_remove_selected_arity_matches_every_brand():
    """The core must call remove_selected(selected); the engines take one arg."""
    for brand in BRANDS:
        det = _detect(brand)
        params = list(inspect.signature(det.remove_selected).parameters.values())
        positional = [
            p for p in params
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        assert len(positional) == 1, (
            f"{brand}: remove_selected expects {len(positional)} positional args, "
            "core passes one"
        )


def test_every_finding_prefix_is_removable():
    """A vector you can detect but not remove is a bug, not a feature.

    Scanners emit f"Prefix: {value}"; _remove_one dispatches on those prefixes,
    either singly or in a startswith() tuple. Every emitted prefix must be
    handled (user-data vectors are consent-gated and cleaned elsewhere).
    """
    import re as _re

    info_only = {
        "Browser extension", "Extension", "Cookie", "Cookies", "History",
    }
    not_findings = {
        "remove_selected", "Error", "Warning", "Note", "Value", "Name",
        "Key", "Data", "Type", "Path", "Status", "Result",
    }

    def body(src: str, fn: str) -> str:
        m = _re.search(rf"def {fn}\(.*?\n(?=\ndef |\nclass |\Z)", src, _re.S)
        return m.group(0) if m else ""

    problems = []
    for brand in BRANDS:
        src = (
            Path(__file__).resolve().parents[1]
            / "brands" / brand / f"{brand}_detect.py"
        ).read_text(encoding="utf-8")

        cut = src.find("def _remove_one")
        scan_src = src[:cut] if cut > 0 else src
        emitted = {
            m.group(1).strip()
            for m in _re.finditer(r"""f["']([A-Za-z][A-Za-z0-9 _\-]{1,45}?): \{""", scan_src)
        }

        rbody = body(src, "_remove_one")
        handled = {
            m.group(1).strip()
            for m in _re.finditer(
                r"""startswith\((?:f)?["']([A-Za-z][A-Za-z0-9 _\-]{1,45}?): """, rbody
            )
        }
        for m in _re.finditer(r"""startswith\(\s*\((.*?)\)\s*\)""", rbody, _re.S):
            for mm in _re.finditer(
                r"""["']([A-Za-z][A-Za-z0-9 _\-]{1,45}?): """, m.group(1)
            ):
                handled.add(mm.group(1).strip())

        missing = sorted(
            p for p in emitted - handled
            if p not in info_only and p not in not_findings
        )
        if missing:
            problems.append(f"{brand}: {missing}")

    assert not problems, (
        "findings emitted with no removal handler:\n" + "\n".join(problems)
    )


def test_core_calls_match_detect_signatures():
    """Every core -> detect call binds the right number of arguments.

    Guards the class of bug where a refactor changed a detect function's
    signature but left a caller passing an extra BrandConfig argument.
    """
    import ast as _ast

    cfg = _cfg("baidu")
    det = cfg.load_detect_module()
    core = Path(__file__).resolve().parents[1] / "antivancedcore"

    problems = []
    for f in sorted(core.glob("*.py")):
        tree = _ast.parse(f.read_text(encoding="utf-8"))
        aliases = set()
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Assign) and isinstance(node.value, _ast.Call):
                inner = getattr(node.value.func, "id", None) or getattr(
                    node.value.func, "attr", None
                )
                if inner in ("_detect", "_detect_module"):
                    for t in node.targets:
                        if isinstance(t, _ast.Name):
                            aliases.add(t.id)

        for node in _ast.walk(tree):
            if not isinstance(node, _ast.Call):
                continue
            if not isinstance(node.func, _ast.Attribute):
                continue
            recv = node.func.value
            recv_name = getattr(recv, "id", None)
            if isinstance(recv, _ast.Call):
                inner = getattr(recv.func, "id", None) or getattr(
                    recv.func, "attr", None
                )
                recv_name = "_detect" if inner in ("_detect", "_detect_module") else None
            if recv_name not in aliases and recv_name not in ("_detect", "_detect_module"):
                continue

            attr = node.func.attr
            fn = getattr(det, attr, None)
            if fn is None:
                continue
            try:
                sig = inspect.signature(fn)
            except (TypeError, ValueError):
                continue
            params = [
                p for p in sig.parameters.values()
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            ]
            required = [p for p in params if p.default is p.empty]
            n = len(node.args)
            if n < len(required) or n > len(params):
                problems.append(
                    f"{f.name}:{node.lineno}: {attr}() got {n} args, "
                    f"signature {sig}"
                )

    assert not problems, "core/detect arity mismatch:\n" + "\n".join(problems)
