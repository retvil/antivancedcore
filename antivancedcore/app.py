"""Shared GUI for the Anti<Brand> editions (brand-agnostic core).

Entry points (main.py, main_extended.py) call ``run(cfg, profile_name)`` with a
:class:`~antivancedcore.brand.BrandConfig` and a product profile from
``profiles``; the profile selects the scan scope and the product name.

Every brand-specific value (install paths, process kill-list, detect module,
policy keys, i18n consent text, logo, GitHub URL) is read from ``cfg``, so this
single module serves all Anti<Brand>Vanced products.
"""

import ctypes
import os
import shutil
import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox

import psutil
import ttkbootstrap as ttk

import antivancedcore.backup as backup
import antivancedcore.engines as engines
import antivancedcore.exclusions as exclusions
import antivancedcore.policies as policies
import antivancedcore.products_detect as products_detect
import antivancedcore.profiles as profiles
import antivancedcore.report as report
import antivancedcore.restore as restore
import antivancedcore.translations as translations
import antivancedcore.updater as updater
import antivancedcore.watchdog as watchdog
from antivancedcore.brand import BrandConfig

TEXT_MUTED = "#6b7280"
STATUS_COLORS = {
    "ok": "#15803d",
    "warn": "#b45309",
    "info": "#0369a1",
    "bad": "#b91c1c",
}

# Browser processes that lock profile databases during hijack removal
BROWSER_PROCESSES = {
    "chrome.exe", "msedge.exe", "brave.exe", "vivaldi.exe", "opera.exe",
    "firefox.exe", "waterfox.exe", "browser.exe",
}

# Set by run(); module-level functions below read these.
CFG: BrandConfig = None          # type: ignore
PROFILE: str = profiles.EXTENDED
language: str = ""
root: ttk.Window
status_label: ttk.Label
findings_box: tk.Text
engine_menu: ttk.Combobox

last_findings: list[str] = []


def t(key: str) -> str:
    """Translate a key for the current UI language, filling {brand}."""
    text = translations.t(language, key)
    return translations.fill_brand(text, CFG.name)


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (OSError, AttributeError):
        return False


def update_status(status, color=STATUS_COLORS["info"]):
    status_label.configure(text=status, foreground=color)
    if "status_dot" in globals():
        status_dot.configure(foreground=color)


def _set_findings_count(n):
    """Update the live findings count label (no-op when the widget isn't up yet)."""
    if "findings_label" in globals():
        findings_label.configure(
            text=t("findings_count").format(n) if n else t("findings_label")
        )


def _render_findings(lines):
    findings_box.configure(state=tk.NORMAL)
    findings_box.delete("1.0", tk.END)
    for line in lines:
        findings_box.insert(tk.END, line + "\n")
    findings_box.configure(state=tk.DISABLED)
    _set_findings_count(len(lines))


def run_in_ui(fn):
    """Run a UI-touching callable on the main thread (tkinter is not thread-safe)."""
    root.after(0, fn)


def _detect():
    """Import the brand's detect module (the scan/remove engine)."""
    return CFG.load_detect_module()


def _brand_paths():
    """Brand install paths (from the detect module's <BRAND>_PATHS constant).

    Falls back to the universal ``scan_install_paths()`` when a detect module
    does not expose a ``*_PATHS`` candidate list.
    """
    det = _detect()
    for name in dir(det):
        if name.endswith("_PATHS") and not name.startswith("UNINSTALL"):
            return list(getattr(det, name))
    return det.scan_install_paths()


def check_registry_for_brand():
    found = _detect().scan_uninstall_entries()
    if found:
        update_status(t("reg_found"), STATUS_COLORS["ok"])
        messagebox.showinfo(t("title"), t("reg_found"))
    else:
        update_status(t("reg_not_found"), STATUS_COLORS["bad"])
        messagebox.showwarning(t("title"), t("reg_not_found"))


def kill_brand_processes():
    killed = False
    extended = PROFILE == profiles.EXTENDED
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            name = proc.info["name"]
            if extended:
                hit = products_detect.is_product_process(CFG, name)
            else:
                hit = bool(name) and name.lower() in {n.lower() for n in CFG.kill_names}
                if not hit:
                    exe = (proc.info.get("exe") or "").lower()
                    hit = CFG.browser_process_marker in exe if CFG.browser_process_marker else False
            if hit:
                proc.kill()
                killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        update_status(t("status_killed"), STATUS_COLORS["ok"])
        messagebox.showinfo(t("title"), t("success_kill"))
    else:
        update_status(t("status_no_proc"), STATUS_COLORS["warn"])
        messagebox.showwarning(t("title"), t("not_found_warning"))


def check_brand_browser():
    def task():
        run_in_ui(lambda: update_status(t("status_searching"), STATUS_COLORS["info"]))
        hits = [p for p in _brand_paths() if os.path.exists(p)]
        if hits:
            run_in_ui(lambda: update_status(t("status_found").format(hits[0]), STATUS_COLORS["ok"]))
        else:
            run_in_ui(lambda: update_status(t("status_not_found"), STATUS_COLORS["bad"]))

    threading.Thread(target=task, daemon=True).start()


def uninstall_brand_browser():
    hits = [p for p in _brand_paths() if os.path.exists(p)]
    if not hits:
        messagebox.showwarning(t("title"), t("delete_first"))
        return
    target = hits[0]

    def task():
        try:
            shutil.rmtree(target, ignore_errors=False)
        except shutil.Error as exc:
            locked = "; ".join(str(f) for f in getattr(exc, "args", ())[:3])

            def fail_locked():
                update_status(t("delete_fail"), STATUS_COLORS["bad"])
                messagebox.showerror(t("title"), f"{t('delete_fail')}\n{locked}")

            run_in_ui(fail_locked)
            return
        except PermissionError:

            def fail_admin():
                update_status(t("delete_fail"), STATUS_COLORS["bad"])
                messagebox.showerror(t("title"), t("delete_fail_admin"))

            run_in_ui(fail_admin)
            return
        except OSError as exc:

            def fail_other():
                update_status(t("delete_fail"), STATUS_COLORS["bad"])
                messagebox.showerror(t("title"), f"{t('delete_fail')}\nError: {exc}")

            run_in_ui(fail_other)
            return
        if not os.path.exists(target):
            _detect().remove_uninstall_entries()
            backup.log_action(CFG, f"uninstall_brand_browser: removed {target}")

            def done():
                update_status(t("delete_success"), STATUS_COLORS["ok"])
                messagebox.showinfo(t("title"), t("delete_success"))

            run_in_ui(done)
        else:

            def fail_locked2():
                update_status(t("delete_fail"), STATUS_COLORS["bad"])
                messagebox.showerror(t("title"), f"{t('delete_fail')}\nFiles locked")

            run_in_ui(fail_locked2)

    threading.Thread(target=task, daemon=True).start()


def scan_hijacks():
    """Scan the profile's brand hijack vectors, show findings, offer selection."""

    def task():
        run_in_ui(lambda: update_status(t("status_searching"), STATUS_COLORS["info"]))
        findings = _detect().scan_all(PROFILE, CFG)

        def done():
            global last_findings
            last_findings = findings
            if findings:
                _render_findings(
                    [t("hijack_found").format(len(findings))] + [f"•  {f}" for f in findings]
                )
                update_status(t("hijack_found").format(len(findings)), STATUS_COLORS["warn"])
                _open_selection_dialog(findings)
            else:
                _render_findings([t("hijack_clean")])
                update_status(t("hijack_clean"), STATUS_COLORS["ok"])

        run_in_ui(done)

    threading.Thread(target=task, daemon=True).start()


def _running_browsers() -> list[str]:
    names = set()
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info["name"] or "").lower()
            if name in BROWSER_PROCESSES:
                names.add(name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(names)


def _kill_browsers() -> None:
    for proc in psutil.process_iter(["name"]):
        try:
            if (proc.info["name"] or "").lower() in BROWSER_PROCESSES:
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def remove_hijacks():
    """Open the selection dialog for the last scan results."""
    if not last_findings:
        scan_hijacks()
        return
    _open_selection_dialog(last_findings)


def _remove_selected_task(selected: list[str]) -> None:
    """Background removal of the user-selected findings + result reporting."""
    removed, failed = _detect().remove_selected(selected)

    def done():
        if removed:
            update_status(t("hijack_removed").format(len(removed)), STATUS_COLORS["ok"])
        else:
            update_status(t("hijack_none"), STATUS_COLORS["info"])
        if failed:
            message = t("hijack_remove_fail").format("\n".join(failed))
            if backup._session_dir is not None and any(backup._session_dir.rglob("*")):
                message += "\n\n" + t("backup_done").format(path=CFG.base_dir)
            messagebox.showwarning(t("title"), message)
            if messagebox.askyesno(t("title"), t("open_log_ask")):
                os.startfile(str(CFG.base_dir))
        if removed:
            messagebox.showinfo(t("title"), t("hijack_removed").format("\n".join(removed)))
        elif not failed:
            messagebox.showinfo(t("title"), t("hijack_none"))

    run_in_ui(done)
    run_in_ui(scan_hijacks)


def _open_selection_dialog(findings: list[str]) -> None:
    """Modal dialog: pick findings to remove, manage exclusions."""
    excluded = exclusions.load(CFG)
    dialog = ttk.Toplevel(title=t("select_title"), size=(620, 520), minsize=(520, 420))
    dialog.transient(root)
    dialog.grab_set()

    ttk.Label(
        dialog,
        text=t("select_hint"),
        wraplength=580,
        justify="left",
        font=("Segoe UI", 10),
        foreground=TEXT_MUTED,
        padding=(12, 10, 12, 6),
    ).pack(fill="x")

    # Scrollable checkbox list
    outer = ttk.Frame(dialog)
    outer.pack(fill="both", expand=True, padx=12, pady=(0, 8))
    canvas = tk.Canvas(outer, highlightthickness=0)
    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    list_frame = ttk.Frame(canvas, padding=(4, 4, 16, 4))
    list_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=list_frame, anchor="nw", width=560)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    vars_by_finding: dict[str, tk.BooleanVar] = {}
    for finding in findings:
        var = tk.BooleanVar(value=not exclusions.is_excluded(CFG, finding, excluded))
        vars_by_finding[finding] = var
        tk.Checkbutton(
            list_frame,
            text=finding,
            variable=var,
            anchor="w",
            justify="left",
            wraplength=520,
            font=("Segoe UI", 9),
            bg="#ffffff",
        ).pack(fill="x", anchor="w", pady=1)

    buttons = ttk.Frame(dialog, padding=(12, 4, 12, 12))
    buttons.pack(fill="x", side="bottom")

    def close():
        canvas.unbind_all("<MouseWheel>")
        dialog.destroy()

    def on_remove():
        selected = [f for f, var in vars_by_finding.items() if var.get()]
        if not selected:
            messagebox.showinfo(t("select_title"), t("select_none"), parent=dialog)
            return
        if any(f.startswith(CFG.consent_prefixes) for f in selected):
            if not messagebox.askyesno(t("title"), t("consent_confirm"), parent=dialog):
                return
        running = _running_browsers()
        if running and not messagebox.askyesno(t("title"), t("close_browsers_confirm")):
            return
        if running:
            _kill_browsers()
        close()
        threading.Thread(target=_remove_selected_task, args=(selected,), daemon=True).start()

    def on_exclude():
        unchecked = [f for f, var in vars_by_finding.items() if not var.get()]
        for finding in unchecked:
            exclusions.add(CFG, finding)
        update_status(t("exclusions_saved").format(len(unchecked)), STATUS_COLORS["info"])

    def on_reset():
        exclusions.clear(CFG)
        for var in vars_by_finding.values():
            var.set(True)
        update_status(t("exclusions_cleared"), STATUS_COLORS["info"])

    ttk.Button(buttons, bootstyle="danger", text=t("select_remove_btn"), command=on_remove).pack(
        side="left", fill="x", expand=True, padx=(0, 6)
    )
    ttk.Button(buttons, bootstyle="secondary", text=t("select_exclude_btn"), command=on_exclude).pack(
        side="left", padx=(0, 6)
    )
    ttk.Button(
        buttons, bootstyle="secondary", text=t("select_reset_exclusions_btn"), command=on_reset
    ).pack(side="left", padx=(0, 6))
    ttk.Button(buttons, bootstyle="secondary", text=t("select_cancel_btn"), command=close).pack(
        side="left"
    )


def apply_search_policy():
    """Hard-enforce the selected engine in all Chromium browsers + Firefox."""
    engine_name = engine_menu.get()
    if not engine_name:
        return
    engine = engines.get_engine(engine_name)

    def task():
        applied, failed = policies.apply_chromium(CFG, engine)
        ff_applied, ff_failed = policies.apply_firefox(engine)
        applied += ff_applied
        failed += ff_failed
        backup.log_action(
            CFG, f"apply_search_policy: engine={engine.name} applied={applied} failed={failed}"
        )

        def done():
            update_status(t("policy_applied").format(", ".join(applied) or "-"), STATUS_COLORS["ok"])
            if failed:
                messagebox.showwarning(t("title"), t("policy_failed").format(", ".join(failed)))
            else:
                messagebox.showinfo(t("title"), t("policy_applied").format(", ".join(applied)))

        run_in_ui(done)

    threading.Thread(target=task, daemon=True).start()


def restore_backup_ui():
    """GUI action: replay the last backup session."""

    def task():
        result = restore.restore(CFG)

        def done():
            if result["reg"] + result["tasks"] + result["files"] > 0:
                summary = f"reg={result['reg']} tasks={result['tasks']} files={result['files']}"
                update_status(t("restore_done").format(summary), STATUS_COLORS["ok"])
                if result["errors"]:
                    messagebox.showwarning(t("title"), "\n".join(result["errors"]))
                else:
                    messagebox.showinfo(t("title"), t("restore_done").format(summary))
            else:
                update_status(t("restore_none"), STATUS_COLORS["warn"])
                messagebox.showinfo(t("title"), t("restore_none"))

        run_in_ui(done)

    if not messagebox.askyesno(t("title"), t("restore_confirm")):
        return
    threading.Thread(target=task, daemon=True).start()


def export_report_ui():
    """GUI action: write JSON + HTML report of the last scan."""

    def task():
        try:
            json_p, html_p = report.default_report_paths(CFG)
            report.export_json(last_findings, PROFILE, CFG.app_version, json_p)
            report.export_html(last_findings, PROFILE, CFG.app_version, html_p)
            ok = True
            where = str(json_p)
        except OSError:
            ok = False
            where = ""

        def done():
            if ok:
                update_status(t("export_done").format(where), STATUS_COLORS["ok"])
                messagebox.showinfo(t("title"), t("export_done").format(where))
            else:
                update_status(t("export_fail"), STATUS_COLORS["bad"])
                messagebox.showerror(t("title"), t("export_fail"))

        run_in_ui(done)

    threading.Thread(target=task, daemon=True).start()


def toggle_watchdog_ui(checked: bool):
    """GUI action: install/remove the daily policy watchdog task."""
    engine_name = engine_menu.get()

    def task():
        try:
            if checked:
                tid = watchdog.install(CFG, engine_name)
                ok, msg = True, t("watchdog_on").format(tid)
            else:
                watchdog.remove(CFG)
                ok, msg = True, t("watchdog_off")
        except Exception as exc:  # noqa: BLE001 - surfaced in the UI
            ok, msg = False, t("watchdog_fail").format(str(exc)[:120])

        def done():
            if ok:
                update_status(msg, STATUS_COLORS["ok"])
            else:
                update_status(msg, STATUS_COLORS["bad"])

        run_in_ui(done)

    threading.Thread(target=task, daemon=True).start()


def check_update_ui():
    """Background check for a newer GitHub release; expose it in the footer."""

    def task():
        latest = updater.fetch_latest_version(CFG)
        if not updater.is_newer(CFG, latest):
            return

        def done():
            update_link.configure(
                text=t("update_label").format(latest), foreground=STATUS_COLORS["ok"]
            )
            update_link.bind(
                "<Button-1>",
                lambda e: webbrowser.open(f"https://github.com/{CFG.repo}/releases/latest"),
            )

        run_in_ui(done)

    threading.Thread(target=task, daemon=True).start()


def remove_brand_policies():
    """Strip the brand's DefaultSearchProvider policy values from the registry."""

    def task():
        cleaned = policies.remove_brand_search_policies(CFG)
        backup.log_action(CFG, f"remove_brand_policies: cleaned={cleaned}")

        def done():
            if cleaned:
                update_status(t("policy_cleaned").format(", ".join(cleaned)), STATUS_COLORS["ok"])
                messagebox.showinfo(t("title"), t("policy_cleaned").format("\n".join(cleaned)))
            else:
                update_status(t("policy_nothing"), STATUS_COLORS["info"])
                messagebox.showinfo(t("title"), t("policy_nothing"))

        run_in_ui(done)

    threading.Thread(target=task, daemon=True).start()


def run(cfg: BrandConfig, profile_name: str, brands: dict | None = None) -> None:
    """Build the GUI for one product profile and start the main loop.

    Args:
        cfg: Fully-populated BrandConfig for the target brand (default target
            when a picker is shown).
        profile_name: profiles.VANCED or profiles.EXTENDED.
        brands: Optional ``{brand_dir: BrandConfig}`` registry. When given, a
            brand selector is shown at the top of the window; choosing one
            re-binds ``CFG`` and refreshes the whole interface. This is what
            makes the single multi-brand EXE possible.
    """
    global CFG, PROFILE, language
    global root, status_label, findings_box, engine_menu, main_label, footer_label
    global status_dot, findings_label, findings_scroll, actions_card
    global btn_check, btn_registry, btn_kill, btn_delete
    global btn_hijack, btn_hijack_remove, policy_card, hijack_card, maint_card
    global btn_policy, btn_unbaidu_policy, update_link
    global btn_restore, btn_export, chk_watchdog

    CFG = cfg
    PROFILE = profiles.validate(profile_name)
    language = translations.detect_system_language()

    # --- GUI ---
    # Wider window with breathing room; minsize keeps every card usable.
    root = ttk.Window(themename="flatly", size=(480, 780), minsize=(420, 720))
    root.title(t("title"))

    # App icon (logo.ico next to the brand assets)
    _icon = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logo.ico")
    if os.path.exists(_icon):
        try:
            root.iconbitmap(_icon)
        except tk.TclError:
            pass

    style = ttk.Style()
    style.configure("Card.TFrame", background="#ffffff", relief="flat")
    style.configure("Card.TLabel", background="#ffffff")
    style.configure("CardTitle.TLabel", background="#ffffff", font=("Segoe UI", 11, "bold"))
    style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground="#334155")
    style.configure("Muted.TLabel", background="#ffffff", foreground=TEXT_MUTED,
                    font=("Segoe UI", 9))

    def on_language_change(choice):
        global language
        for code, display in translations.LANG_DISPLAY_NAMES.items():
            if display == choice:
                language = code
                break
        update_ui()

    # Brand selector (multi-brand mode only): the headline feature, so it gets
    # a hero position. Shown above the title, full width, large font.
    brand_menu = None
    if brands:
        brand_bar = ttk.Labelframe(root, text=t("brand_label"), padding=(16, 10, 16, 10))
        brand_bar.pack(fill="x", padx=20, pady=(14, 0))

        brand_names = [b.name for b in brands.values()]
        brand_menu = ttk.Combobox(
            brand_bar,
            values=brand_names,
            state="readonly",
            font=("Segoe UI", 13, "bold"),
        )
        brand_menu.set(cfg.name)
        brand_menu.pack(fill="x")

        def on_brand_change(choice):
            global CFG
            for b in brands.values():
                if b.name == choice:
                    CFG = b
                    last_findings.clear()
                    _render_findings([])
                    update_ui()
                    break

        brand_menu.bind("<<ComboboxSelected>>", on_brand_change)

    # Language selector: single dropdown, top-right
    lang_bar = ttk.Frame(root, padding=(20, 10, 20, 0))
    lang_bar.pack(fill="x")

    lang_menu = ttk.Combobox(
        lang_bar,
        values=list(translations.LANG_DISPLAY_NAMES.values()),
        state="readonly",
        width=13,
        font=("Segoe UI", 11),
    )
    lang_menu.set(translations.LANG_DISPLAY_NAMES[language])
    lang_menu.bind("<<ComboboxSelected>>", on_language_change)
    lang_menu.pack(side="right")

    # Title: large, centered
    main_label = ttk.Label(root, font=("Segoe UI", 20, "bold"), anchor="center")
    main_label.pack(fill="x", padx=20, pady=(10, 12))

    # Quick actions: 2x2 grid instead of 4 full-width stacked rows
    actions_card = ttk.Labelframe(root, text=t("quick_actions"), padding=(14, 10, 14, 12))
    actions_card.pack(fill="x", padx=20, pady=(4, 6))

    actions = ttk.Frame(actions_card)
    actions.pack(fill="x")
    for col in (0, 1):
        actions.columnconfigure(col, weight=1, uniform="col")
    actions.rowconfigure(0, weight=1, uniform="row")

    btn_check = ttk.Button(actions, bootstyle="info", command=check_brand_browser)
    btn_check.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=3)

    btn_registry = ttk.Button(actions, bootstyle="secondary", command=check_registry_for_brand)
    btn_registry.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=3)

    btn_kill = ttk.Button(actions, bootstyle="info", command=kill_brand_processes)
    btn_kill.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=3)

    btn_delete = ttk.Button(actions, bootstyle="danger", command=uninstall_brand_browser)
    btn_delete.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=3)

    # Search hijacks: the main workflow, visually prominent with a scrollable
    # findings list and a live count.
    hijack_card = ttk.Labelframe(root, text=t("hijack_section"), padding=(14, 10, 14, 12))
    hijack_card.pack(fill="x", padx=20, pady=(4, 6))

    btn_hijack = ttk.Button(hijack_card, bootstyle="primary", command=scan_hijacks)
    btn_hijack.pack(fill="x", pady=(0, 6))

    findings_header = ttk.Frame(hijack_card)
    findings_header.pack(fill="x", pady=(0, 4))

    findings_label = ttk.Label(
        findings_header, text="", style="Muted.TLabel", font=("Segoe UI", 9)
    )
    findings_label.pack(side="left")

    findings_wrap = ttk.Frame(hijack_card)
    findings_wrap.pack(fill="x", pady=(0, 6))

    findings_box = tk.Text(
        findings_wrap,
        height=5,
        wrap="word",
        font=("Consolas", 10),
        relief="flat",
        background="#f8fafc",
        foreground="#1f2937",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground="#e2e8f0",
        padx=8,
        pady=6,
    )
    findings_box.pack(side="left", fill="both", expand=True)

    findings_scroll = ttk.Scrollbar(findings_wrap, orient="vertical", command=findings_box.yview)
    findings_scroll.pack(side="right", fill="y")
    findings_box.configure(yscrollcommand=findings_scroll.set)
    findings_box.configure(state=tk.DISABLED)

    btn_hijack_remove = ttk.Button(hijack_card, bootstyle="warning", command=remove_hijacks)
    btn_hijack_remove.pack(fill="x", pady=(0, 2))

    # Default search policy
    policy_card = ttk.Labelframe(
        root, text=t("policy_section"), padding=(14, 10, 14, 12)
    )
    policy_card.pack(fill="x", padx=20, pady=(4, 6))

    policy_row = ttk.Frame(policy_card)
    policy_row.pack(fill="x", pady=(4, 8))

    engine_menu = ttk.Combobox(
        policy_row, values=list(engines.ENGINE_NAMES), state="readonly", font=("Segoe UI", 11)
    )
    engine_menu.set(engines.ENGINE_NAMES[0])
    engine_menu.pack(fill="x")

    btn_policy = ttk.Button(policy_card, bootstyle="success", command=apply_search_policy)
    btn_policy.pack(fill="x", pady=(0, 6))

    btn_unbaidu_policy = ttk.Button(
        policy_card, bootstyle="secondary", command=remove_brand_policies
    )
    btn_unbaidu_policy.pack(fill="x", pady=(0, 2))

    # Maintenance: restore / export / watchdog
    maint_card = ttk.Labelframe(root, text=t("maintenance_section"), padding=(14, 10, 14, 12))
    maint_card.pack(fill="x", padx=20, pady=(4, 6))

    maint_row = ttk.Frame(maint_card)
    maint_row.pack(fill="x", pady=(2, 2))
    for col in (0, 1):
        maint_row.columnconfigure(col, weight=1, uniform="col")

    btn_restore = ttk.Button(maint_row, bootstyle="secondary", command=restore_backup_ui)
    btn_restore.grid(row=0, column=0, sticky="ew", padx=(0, 4))

    btn_export = ttk.Button(maint_row, bootstyle="secondary", command=export_report_ui)
    btn_export.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    watchdog_var = tk.BooleanVar(value=watchdog.is_installed(CFG))
    chk_watchdog = ttk.Checkbutton(
        maint_card,
        variable=watchdog_var,
        command=lambda: toggle_watchdog_ui(watchdog_var.get()),
    )
    chk_watchdog.pack(fill="x", pady=(4, 2))

    # Status bar: colored dot indicator + text, above the footer
    status_bar = ttk.Frame(root, padding=(20, 8, 20, 6))
    status_bar.pack(side="bottom", fill="x")

    status_dot = tk.Label(
        status_bar, text="●", font=("Segoe UI", 10),
        foreground=STATUS_COLORS["info"], bg="#ffffff",
    )
    status_dot.pack(side="left", padx=(0, 8))

    status_label = ttk.Label(
        status_bar, font=("Segoe UI", 10), justify="left", anchor="w"
    )
    status_label.pack(side="left", fill="x", expand=True)

    # Footer: product identity + GitHub + auto-update indicator
    footer = ttk.Frame(root, padding=(16, 2, 16, 10))
    footer.pack(side="bottom", fill="x")

    footer_label = ttk.Label(
        footer,
        font=("Segoe UI", 9),
        foreground=TEXT_MUTED,
        text=f"{cfg.product_names[PROFILE]} {cfg.app_version} by {cfg.app_author}",
    )
    footer_label.pack(side="left")

    update_link = ttk.Label(
        footer, font=("Segoe UI", 9, "underline"), foreground=STATUS_COLORS["ok"],
        text="", cursor="hand2",
    )
    update_link.pack(side="left", padx=(10, 0))

    github_link = ttk.Label(
        footer,
        font=("Segoe UI", 9, "underline"),
        foreground="#0369a1",
        text="GitHub",
        cursor="hand2",
    )
    github_link.pack(side="right")
    github_link.bind(
        "<Button-1>", lambda e: webbrowser.open(f"https://github.com/{CFG.repo}")
    )

    def _retune_status(event=None):
        """Keep the status text wrapping inside the bar at any width."""
        width = status_label.winfo_width()
        if width > 1:
            new_wrap = max(120, width - 20)
            if status_label.cget("wraplength") != new_wrap:
                status_label.configure(wraplength=new_wrap)

    status_bar.bind("<Configure>", _retune_status)

    def update_ui():
        """Refresh every translatable text in the interface."""
        root.title(t("title"))
        main_label.configure(text=t("title"))
        btn_check.configure(text=t("search_btn"))
        btn_registry.configure(text=t("registry_check_btn"))
        btn_kill.configure(text=t("kill_btn"))
        btn_delete.configure(text=t("delete_btn"))
        btn_hijack.configure(text=t("hijack_btn"))
        btn_hijack_remove.configure(text=t("hijack_remove_btn"))
        policy_card.configure(text=t("policy_section"))
        hijack_card.configure(text=t("hijack_section"))
        btn_policy.configure(text=t("policy_btn"))
        btn_unbaidu_policy.configure(text=t("policy_unbaidu_btn"))
        maint_card.configure(text=t("maintenance_section"))
        btn_restore.configure(text=t("restore_btn"))
        btn_export.configure(text=t("export_btn"))
        chk_watchdog.configure(text=t("watchdog_label"))
        actions_card.configure(text=t("quick_actions"))
        update_status(t("status_wait"))
        _render_findings([])  # stale findings are in the previous language
        # Footer always reflects the currently selected brand.
        footer_label.configure(
            text=f"{CFG.product_names[PROFILE]} {CFG.app_version} "
                 f"by {CFG.app_author}"
        )

    update_ui()

    if not is_admin():
        update_status(t("warn_no_admin"), STATUS_COLORS["warn"])

    # Fire the background update check after the first paint
    root.after(800, check_update_ui)

    root.mainloop()
