"""BrandConfig for QQ (brands/qq/)."""

from antivancedcore.brand import BrandConfig

CFG = BrandConfig(
    name='QQ',
    detect_module='qq_detect',
    repo='retvil/AntiQQVanced',
    appdata_dir='AntiQQVanced',
    app_version="1.4.0",
    app_author="Nod33Eset",
    kill_names=('qqbrowser.exe', 'qqcloud.exe'),
    browser_process_marker='qq',
    consent_prefixes=('Roaming: ', 'Local data: ', 'DNS: ', 'Extension: ', 'Cookies: ', 'Defender exclusion: '),
    policy_vendor_key='SOFTWARE\\Policies\\QQ\\QQ Browser',
    policy_domain='qq.com',
    remove_func_name="remove_qq_search_policies",
    task_name='\\AntiQQ\\PolicyWatch',
    product_markers=('qq', 'qqbrowser.exe', 'qqcloud.exe'),
    appx_match_pattern='qq|腾讯|tencent',
    dns_ips=frozenset(),
    browser_dir_name='qqbrowser',
    product_names={'vanced': 'AntiQQVanced', 'extended': 'AntiQQExtended'},
)

__all__ = ["CFG", "BrandConfig"]
