"""BrandConfig for 2345 (brands/ant2345/)."""

from antivancedcore.brand import BrandConfig

CFG = BrandConfig(
    name='2345',
    detect_module='ant2345_detect',
    repo='retvil/Anti2345Vanced',
    appdata_dir='Anti2345Vanced',
    app_version="1.4.0",
    app_author="Nod33Eset",
    kill_names=('2345explorer.exe', '2345cloud.exe'),
    browser_process_marker='2345',
    consent_prefixes=('Roaming: ', 'Local data: ', 'DNS: ', 'Extension: ', 'Cookies: ', 'Defender exclusion: '),
    policy_vendor_key='SOFTWARE\\Policies\\2345\\2345 Browser',
    policy_domain='2345.com',
    remove_func_name="remove_2345_search_policies",
    task_name='\\Anti2345\\PolicyWatch',
    product_markers=('2345', '2345explorer.exe', '2345cloud.exe'),
    appx_match_pattern='2345',
    dns_ips=frozenset(),
    browser_dir_name='2345explorer',
    product_names={'vanced': 'Anti2345Vanced', 'extended': 'Anti2345Extended'},
)

__all__ = ["CFG", "BrandConfig"]
