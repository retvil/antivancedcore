"""BrandConfig for Naver (brands/naver/)."""

from antivancedcore.brand import BrandConfig

CFG = BrandConfig(
    name='Naver',
    detect_module='naver_detect',
    repo='retvil/AntiNaverVanced',
    appdata_dir='AntiNaverVanced',
    app_version="1.4.0",
    app_author="Nod33Eset",
    kill_names=('whale.exe', 'navercloud.exe'),
    browser_process_marker='whale',
    consent_prefixes=('Roaming: ', 'Local data: ', 'DNS: ', 'Extension: ', 'Cookies: ', 'Defender exclusion: '),
    policy_vendor_key='SOFTWARE\\Policies\\Naver\\Whale',
    policy_domain='naver.com',
    remove_func_name="remove_naver_search_policies",
    task_name='\\AntiNaver\\PolicyWatch',
    product_markers=('naver', 'whale.exe', 'navercloud.exe'),
    appx_match_pattern='naver|네이버|whale',
    dns_ips=frozenset(),
    browser_dir_name='whale',
    product_names={'vanced': 'AntiNaverVanced', 'extended': 'AntiNaverExtended'},
)

__all__ = ["CFG", "BrandConfig"]
