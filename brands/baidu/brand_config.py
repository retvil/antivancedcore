"""BrandConfig for Baidu (brands/baidu/)."""

from antivancedcore.brand import BrandConfig

CFG = BrandConfig(
    name='Baidu',
    detect_module='baidu_detect',
    repo='retvil/AntiBaiduVanced',
    appdata_dir='AntiBaiduVanced',
    app_version="1.4.0",
    app_author="Nod33Eset",
    kill_names=('baidubrowser.exe', 'baiducloud.exe', 'baidudisk.exe'),
    browser_process_marker='baidu browser',
    consent_prefixes=('Roaming: ', 'BaiduDisk data: ', 'BaiduDisk files: ', 'Local data: ', 'DNS: ', 'Extension: ', 'Cookies: ', 'Defender exclusion: '),
    policy_vendor_key='SOFTWARE\\Policies\\Baidu\\Baidu Browser',
    policy_domain='baidu.com',
    remove_func_name="remove_baidu_search_policies",
    task_name='\\AntiBaidu\\PolicyWatch',
    product_markers=('baidu', 'baidubrowser.exe', 'baiducloud.exe', 'baidudisk.exe'),
    appx_match_pattern='baidu|百度|baidubrowser|baidu\\.com',
    dns_ips=frozenset(('77.88.8.8', '77.88.8.1', '77.88.8.88', '77.88.8.2', '77.88.8.7', '77.88.8.3')),
    browser_dir_name='baidubrowser',
    product_names={'vanced': 'AntiBaiduVanced', 'extended': 'AntiBaiduExtended'},
)

__all__ = ["CFG", "BrandConfig"]
