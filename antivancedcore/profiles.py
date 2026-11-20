"""Product profiles for the Anti<Brand> editions (brand-agnostic).

One codebase, two products per brand:
- VANCED   — brand Browser + brand Search removal (the classic edition)
- EXTENDED — removal of every product of the brand (superset of VANCED)

The ordered scan steps and the "extended-only" step set are shared by every
brand; the brand's own detect module implements the actual steps.
"""

from dataclasses import dataclass

VANCED = "vanced"
EXTENDED = "extended"

# Ordered scan steps for the EXTENDED profile (superset, canonical order).
_EXTENDED_STEPS: tuple[str, ...] = (
    "scan_install_paths",
    "scan_uninstall_entries",
    "scan_default_browser",
    "scan_start_page",
    "scan_start_menu_internet",
    "scan_software_keys",
    "scan_policy_hijack",
    "scan_startup_urls",
    "scan_chromium_profiles",
    "scan_web_data_keywords",
    "scan_firefox_search",
    "scan_firefox_homepage",
    "scan_search_scopes",
    "scan_autostart",
    "scan_scheduled_tasks",
    "scan_services",
    "scan_file_associations",
    "scan_zone_map",
    "scan_registered_apps",
    "scan_shell_overlays",
    "scan_context_menus",
    "scan_startup_approved",
    "scan_app_paths",
    "scan_shortcuts",
    "scan_leftover_dirs",
    "scan_hosts",
    "scan_firewall_rules",
    "scan_uri_protocols",
    "scan_browser_extensions",
    "scan_cookies",
    "scan_openwith",
    "scan_traces",
    "scan_muicache",
    "scan_defender_exclusions",
    "scan_keyboard_layouts",
    "scan_store_apps",
    "scan_product_dirs",
    "scan_local_data_dirs",
    "scan_dns_servers",
)

# Steps that go beyond browser+search and belong to the Extended edition only.
_EXTENDED_ONLY: frozenset[str] = frozenset({
    "scan_shell_overlays",
    "scan_context_menus",
    "scan_leftover_dirs",
    "scan_hosts",
    "scan_firewall_rules",
    "scan_defender_exclusions",
    "scan_keyboard_layouts",
    "scan_store_apps",
    "scan_product_dirs",
    "scan_local_data_dirs",
    "scan_dns_servers",
})

PROFILE_SCANS: dict[str, tuple[str, ...]] = {
    EXTENDED: _EXTENDED_STEPS,
    VANCED: tuple(s for s in _EXTENDED_STEPS if s not in _EXTENDED_ONLY),
}


def validate(profile: str) -> str:
    """Return the profile name if known, raise ValueError otherwise."""
    if profile not in PROFILE_SCANS:
        raise ValueError(f"unknown profile: {profile!r}")
    return profile
