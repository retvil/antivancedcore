"""BrandConfig for UC (brands/ucweb/)."""

from antivancedcore.brand import BrandConfig

CFG = BrandConfig(
    name='UC',
    detect_module='ucweb_detect',
    repo='retvil/AntiUCWebVanced',
    appdata_dir='AntiUCWebVanced',
    app_version="1.4.0",
    app_author="Nod33Eset",
    kill_names=('ucbrowser.exe', 'uccloud.exe'),
    browser_process_marker='uc',
    consent_prefixes=('Roaming: ', 'Local data: ', 'DNS: ', 'Extension: ', 'Cookies: ', 'Defender exclusion: '),
    policy_vendor_key='SOFTWARE\\Policies\\UC\\UC Browser',
    policy_domain='uc.cn',
    remove_func_name="remove_uc_search_policies",
    task_name='\\AntiUC\\PolicyWatch',
    product_markers=('uc', 'ucbrowser.exe', 'uccloud.exe'),
    appx_match_pattern='uc\\b|UC',
    dns_ips=frozenset(),
    browser_dir_name='ucbrowser',
    product_names={'vanced': 'AntiUCVanced', 'extended': 'AntiUCExtended'},
)

__all__ = ["CFG", "BrandConfig"]
