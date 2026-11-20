"""Extended-edition scans: whole products beyond the browser, per brand.

Covers Store (Appx) applications and product install directories under
Program Files that are not the browser itself. All brand-specific values
(product markers, program-file roots, DNS server set, Appx match pattern,
excluded browser dir name) come from a :class:`~antivancedcore.brand.BrandConfig`,
so this module is shared verbatim by every Anti<Brand>Vanced product.

Brand-specific values are read from ``cfg``:
- ``cfg.product_markers``      — process-name markers (incl. browser EXEs)
- ``cfg.product_dirs_roots``  — (program_files_root, local_dir_marker, local_programs_prefix)
- ``cfg.appx_match_pattern``  — regex for Get-AppxPackage -match
- ``cfg.dns_ips``             — brand's own DNS server set (frozenset)
- ``cfg.browser_dir_name``    — excluded browser sub-dir name (lowercase)
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import antivancedcore.backup as backup
from antivancedcore.brand import BrandConfig


def _product_names(cfg: BrandConfig) -> frozenset[str]:
    return frozenset(cfg.product_markers)


def is_product_process(cfg: BrandConfig, name: str | None) -> bool:
    """True if a process belongs to any of the brand's products (Extended kill scope)."""
    lowered = (name or "").lower()
    markers = cfg.product_markers
    return lowered in _product_names(cfg) or any(
        marker in lowered for marker in markers
    )


def _store_apps_ps(cfg: BrandConfig) -> str:
    pattern = cfg.appx_match_pattern or re.escape(cfg.name.lower())
    return (
        "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
        f"Get-AppxPackage | Where-Object {{ $_.Name -match '{pattern}' }}"
        " | ForEach-Object { \"$($_.Name)|$($_.PackageFullName)\" }"
    )


def _parse_appx_output(text: str) -> list[tuple[str, str]]:
    """Parse 'Name|PackageFullName' lines produced by the Appx scan script."""
    result = []
    for line in text.splitlines():
        line = line.strip()
        if "|" in line and line != "|":
            name, _, full_name = line.partition("|")
            if name and full_name:
                result.append((name, full_name))
    return result


def scan_store_apps(cfg: BrandConfig) -> list[str]:
    """Brand Store (Appx) applications installed for the current user."""
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", _store_apps_ps(cfg)],
            capture_output=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    text = proc.stdout.decode("utf-8", errors="replace")
    return [
        f"Store app: {name} ({full_name})"
        for name, full_name in _parse_appx_output(text)
    ]


def remove_store_app(finding: str) -> bool:
    """Uninstall one Store app by its package full name."""
    full_name = finding[len("Store app: "):].rsplit(" (", 1)[0].rstrip(")")
    escaped = full_name.replace("'", "''")
    script = (
        "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
        f"Remove-AppxPackage -Package '{escaped}'"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, timeout=180,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def _product_roots(cfg: BrandConfig) -> list[str]:
    """Program-Files roots for the brand: <PF>\<name> and <PF(x86)>\<name>."""
    name = cfg.name
    roots = [
        rf"C:\Program Files\{name}",
        rf"C:\Program Files (x86)\{name}",
    ]
    return roots


def scan_product_dirs(cfg: BrandConfig) -> list[str]:
    """Non-browser product directories of the brand.

    Covers Program Files\\<name>\\* and per-user installs under
    %LOCALAPPDATA%\\Programs. The browser install path is reported by
    scan_install_paths; everything else is reported here.
    """
    found = []
    browser_dir = (cfg.browser_dir_name or "").lower()
    for base in _product_roots(cfg):
        if not os.path.isdir(base):
            continue
        for entry in os.listdir(base):
            path = os.path.join(base, entry)
            if os.path.isdir(path) and entry.lower() != browser_dir:
                found.append(f"Product dir: {path}")
    local_programs = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")
    prefix = cfg.name.lower()
    if os.path.isdir(local_programs):
        for entry in os.listdir(local_programs):
            low = entry.lower()
            if not low.startswith(prefix):
                continue
            path = os.path.join(local_programs, entry)
            if not os.path.isdir(path):
                continue
            if low == prefix:
                for sub in os.listdir(path):
                    sub_path = os.path.join(path, sub)
                    if os.path.isdir(sub_path) and sub.lower() != browser_dir:
                        found.append(f"Product dir: {sub_path}")
            elif low != browser_dir:
                found.append(f"Product dir: {path}")
    return found


def scan_local_data_dirs(cfg: BrandConfig) -> list[str]:
    """Non-browser brand data directories under %LOCALAPPDATA%\\<name>.

    These hold user data, so the finding is consent-gated.
    """
    base = Path(os.environ.get("LOCALAPPDATA", "")) / cfg.name
    if not base.is_dir():
        return []
    browser_dir = (cfg.browser_dir_name or "").lower()
    return [
        f"Local data: {entry}"
        for entry in sorted(base.iterdir())
        if entry.is_dir() and entry.name.lower() != browser_dir
    ]


def remove_local_data(target: str) -> bool:
    """Delete one non-browser local data directory (exported to backup first)."""
    backup.export_dir(target)
    try:
        shutil.rmtree(target, ignore_errors=False)
        return True
    except OSError:
        return False


def scan_dns_servers(cfg: BrandConfig) -> list[str]:
    """Network adapters configured with the brand's own DNS servers."""
    dns_ips: frozenset[str] = cfg.dns_ips or frozenset()
    if not dns_ips:
        return []
    _dns_ps = (
        "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
        "Get-DnsClientServerAddress -AddressFamily IPv4"
        " | ForEach-Object { \"$($_.InterfaceAlias)|$($_.InterfaceIndex)|$($_.ServerAddresses -join ',')\" }"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", _dns_ps],
            capture_output=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    found = []
    for alias, index, ips in _parse_dns_output(proc.stdout.decode("utf-8", errors="replace")):
        hit = [ip for ip in ips if ip in dns_ips]
        if hit:
            found.append(f"DNS: {alias} (index {index}, {', '.join(hit)})")
    return found


def _parse_dns_output(text: str) -> list[tuple[str, str, list[str]]]:
    """Parse 'alias|index|ip1,ip2' lines produced by the DNS scan script."""
    result = []
    for line in text.splitlines():
        parts = line.strip().split("|")
        if len(parts) != 3:
            continue
        alias, index, ips = parts
        ip_list = [ip for ip in ips.split(",") if ip]
        if alias and index.isdigit() and ip_list:
            result.append((alias, index, ip_list))
    return result


def remove_dns(finding: str) -> bool:
    """Reset one adapter's DNS servers to automatic (DHCP/router defaults)."""
    match = re.search(r"index (\d+)", finding)
    if not match:
        return False
    script = f"Set-DnsClientServerAddress -InterfaceIndex {match.group(1)} -ResetServerAddresses"
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def remove_product_dir(target: str) -> bool:
    """Delete one non-browser product directory (exported to backup first)."""
    backup.export_dir(target)
    try:
        shutil.rmtree(target, ignore_errors=False)
        return True
    except OSError:
        return False
