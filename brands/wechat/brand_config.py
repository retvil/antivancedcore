"""BrandConfig for WeChat (brands/wechat/)."""

from antivancedcore.brand import BrandConfig

CFG = BrandConfig(
    name='WeChat',
    detect_module='wechat_detect',
    repo='retvil/AntiWeChatVanced',
    appdata_dir='AntiWeChatVanced',
    app_version="1.4.0",
    app_author="Nod33Eset",
    kill_names=('wechat.exe', 'wxwork.exe'),
    browser_process_marker='wechat',
    consent_prefixes=('Roaming: ', 'Local data: ', 'DNS: ', 'Extension: ', 'Cookies: ', 'Defender exclusion: '),
    policy_vendor_key='SOFTWARE\\Policies\\WeChat\\WeChat',
    policy_domain='wechat.com',
    remove_func_name="remove_wechat_search_policies",
    task_name='\\AntiWeChat\\PolicyWatch',
    product_markers=('wechat', 'wxwork', '腾讯'),
    appx_match_pattern='wechat|微信|wxwork',
    dns_ips=frozenset(),
    browser_dir_name='wechat',
    product_names={'vanced': 'AntiWeChatVanced', 'extended': 'AntiWeChatExtended'},
)

__all__ = ["CFG", "BrandConfig"]
