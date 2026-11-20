"""CLI entry point for non-interactive (script/Intune) usage.

Usage examples (``<brand>`` is the detect module name from BrandConfig):
    python main.py --scan-only
    python main.py --apply --yes --apply-policy google
    python main.py --restore
    python main.py --install-watchdog google
    python main.py --remove-watchdog
    python main.py --report C:\\reports\\out.json

Exit codes: 0 success, 1 failure, 2 findings-only (scan found items).

All brand-specific behaviour (which detect module, which processes to kill,
which findings are consent-gated) comes from ``BrandConfig``.
"""

import argparse
import importlib
import sys


def _detect_module(cfg):
    """Import and return the brand's detect module (scan/remove engine)."""
    return importlib.import_module(cfg.detect_module)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="antivanced",
        description="Remove the brand's browser/search hijack vectors "
                    "and lock the default search engine.",
    )
    p.add_argument("--scan-only", action="store_true",
                   help="Run the scan and print findings; make no changes.")
    p.add_argument("--apply", action="store_true",
                   help="Perform removal + policy application (destructive).")
    p.add_argument("--apply-policy", metavar="ENGINE",
                   help="Apply the hard policy for ENGINE only "
                        "(e.g. google, bing, duckduckgo).")
    p.add_argument("--yes", action="store_true",
                   help="Auto-confirm all prompts (required for --apply).")
    p.add_argument("--consent-user-data", action="store_true",
                   help="Also remove items that contain user data "
                        "(Disk files, cookies, extensions).")
    p.add_argument("--restore", action="store_true",
                   help="Restore the last backup session (registry/tasks/files).")
    p.add_argument("--install-watchdog", metavar="ENGINE",
                   help="Create a daily scheduled task that re-applies ENGINE policy.")
    p.add_argument("--remove-watchdog", action="store_true",
                   help="Remove the watchdog scheduled task.")
    p.add_argument("--report", metavar="PATH",
                   help="Write JSON findings report to PATH.")
    p.add_argument("--html-report", metavar="PATH",
                   help="Write HTML findings report to PATH.")
    p.add_argument("--list-engines", action="store_true",
                   help="Print available search engines and exit.")
    return p


def _cmd_scan(cfg, profile: str) -> list[str]:
    det = _detect_module(cfg)
    return det.scan_all(profile, cfg)


def _cmd_apply(cfg, args) -> int:
    import backup
    import policies
    from antivancedcore import engines
    import psutil

    det = _detect_module(cfg)

    backup.start_session(cfg)
    # Kill product processes first
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if cfg.kill_names and name in cfg.kill_names:
                proc.kill()
        except Exception:
            pass

    # Removal of selected findings (excluding user-data unless consented)
    findings = _cmd_scan(cfg, args.profile)
    if args.consent_user_data:
        selected = findings
    else:
        selected = [f for f in findings if not f.startswith(det.CONSENT_PREFIXES)]
    removed, failed = det.remove_selected(selected, cfg)
    print(f"removed: {len(removed)} failed: {len(failed)}")

    # Apply policy
    if args.apply_policy:
        engine = engines.get_engine(args.apply_policy)
        applied, pfailed = policies.apply_chromium(cfg, engine)
        ff_applied, ff_failed = policies.apply_firefox(engine)
        applied += ff_applied
        pfailed += ff_failed
        print(f"policy applied: {len(applied)} failed: {len(pfailed)}")
        for f in pfailed:
            print(f"  policy-fail: {f}")
    return 1 if (failed or pfailed) else 0


def _cmd_restore(cfg) -> int:
    from antivancedcore import restore

    result = restore.restore(cfg)
    print(f"restored: reg={result['reg']} tasks={result['tasks']} files={result['files']}")
    for e in result["errors"]:
        print(f"  restore-err: {e}")
    return 1 if result["errors"] and result["reg"] + result["tasks"] + result["files"] == 0 else 0


def _cmd_watchdog(cfg, args) -> int:
    from antivancedcore import watchdog

    if args.install_watchdog:
        try:
            task = watchdog.install(cfg, args.install_watchdog)
            print(f"watchdog installed: {task} (engine={args.install_watchdog})")
            return 0
        except Exception as exc:
            print(f"watchdog install failed: {exc}")
            return 1
    elif args.remove_watchdog:
        watchdog.remove(cfg)
        print("watchdog removed")
        return 0
    return 0


def _cmd_report(cfg, args) -> int:
    from antivancedcore import report

    findings = _cmd_scan(cfg, args.profile)
    if args.report:
        p = report.export_json(findings, args.profile, cfg.app_version, args.report)
        print(f"report: {p}")
    if args.html_report:
        p = report.export_html(findings, args.profile, cfg.app_version, args.html_report)
        print(f"html-report: {p}")
    for f in findings:
        print(f"finding: {f}")
    return 2 if findings else 0


def main(cfg, argv: list[str] | None = None) -> int:
    """Run the CLI. ``cfg`` is a fully-populated BrandConfig."""
    parser = build_parser()
    args = parser.parse_args(argv)
    # profile is set by the caller (main.py / main_extended.py)
    args.profile = getattr(args, "profile", "vanced")

    if args.list_engines:
        from antivancedcore import engines
        for name in engines.ENGINE_NAMES:
            print(name)
        return 0

    if args.scan_only:
        return _cmd_report(cfg, args)

    if args.apply:
        if not args.yes:
            print("--apply requires --yes")
            return 1
        return _cmd_apply(cfg, args)

    if args.restore:
        return _cmd_restore(cfg)

    if args.install_watchdog or args.remove_watchdog:
        return _cmd_watchdog(cfg, args)

    # no action flags: just help
    parser.print_help()
    return 0
