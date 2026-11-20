"""BrandConfig for Tencent Video (brands/tencent/)."""

from antivancedcore.brand import BrandConfig

CFG = BrandConfig(
    name='Tencent Video',
    detect_module='tencent_detect',
    repo='retvil/AntiTencentVideoVanced',
    appdata_dir='AntiTencentVideoVanced',
    app_version="1.4.0",
    app_author="Nod33Eset",
    kill_names=('qqvideo.exe', 'tencentcloud.exe'),
    browser_process_marker='tencent',
    consent_prefixes=('Roaming: ', 'Local data: ', 'DNS: ', 'Extension: ', 'Cookies: ', 'Defender exclusion: '),
    policy_vendor_key='SOFTWARE\\Policies\\Tencent\\TencentVideo',
    policy_domain='tencent.com',
    remove_func_name="remove_tencent video_search_policies",
    task_name='\\AntiTencent\\PolicyWatch',
    product_markers=('tencent', 'qqvideo', '腾讯视频'),
    appx_match_pattern='tencent|qqvideo|腾讯视频',
    dns_ips=frozenset(),
    browser_dir_name='qqvideo',
    product_names={'vanced': 'AntiTencentVanced', 'extended': 'AntiTencentExtended'},
)

__all__ = ["CFG", "BrandConfig"]
