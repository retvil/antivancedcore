"""BrandConfig for Sogou (brands/sogou/)."""

from antivancedcore.brand import BrandConfig

CFG = BrandConfig(
    name='Sogou',
    detect_module='sogou_detect',
    repo='retvil/AntiSogouVanced',
    appdata_dir='AntiSogouVanced',
    app_version="1.4.0",
    app_author="Nod33Eset",
    kill_names=('sogouexplorer.exe', 'sogoucloud.exe', 'sogoudisk.exe'),
    browser_process_marker='sogou',
    consent_prefixes=('Roaming: ', 'Local data: ', 'DNS: ', 'Extension: ', 'Cookies: ', 'Defender exclusion: '),
    policy_vendor_key='SOFTWARE\\Policies\\Sogou\\Sogou Browser',
    policy_domain='sogou.com',
    remove_func_name="remove_sogou_search_policies",
    task_name='\\AntiSogou\\PolicyWatch',
    product_markers=('sogou', 'sogouexplorer.exe', 'sogoucloud.exe'),
    appx_match_pattern='sogou|搜狗|sogou\\.com',
    dns_ips=frozenset(),
    browser_dir_name='sogouexplorer',
    product_names={'vanced': 'AntiSogouVanced', 'extended': 'AntiSogouExtended'},
)

__all__ = ["CFG", "BrandConfig"]
