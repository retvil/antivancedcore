"""BrandConfig for Mail.ru (brands/mailru/)."""

from antivancedcore.brand import BrandConfig

CFG = BrandConfig(
    name='Mail.ru',
    detect_module='mailru_detect',
    repo='retvil/AntiVKGroupVanced',
    appdata_dir='AntiVKGroupVanced',
    app_version="1.4.0",
    app_author="Nod33Eset",
    kill_names=('agent.exe', 'vk_messenger.exe', 'mailru_cloud.exe'),
    browser_process_marker='mail.ru',
    consent_prefixes=('Roaming: ', 'Local data: ', 'DNS: ', 'Extension: ', 'Cookies: ', 'Defender exclusion: '),
    policy_vendor_key='SOFTWARE\\Policies\\Mailru\\Mailru',
    policy_domain='mail.ru',
    remove_func_name="remove_mail.ru_search_policies",
    task_name='\\AntiVKGroup\\PolicyWatch',
    product_markers=('mail.ru', 'vk.com', 'agent'),
    appx_match_pattern='mail\\.ru|vk\\.|vk_messenger',
    dns_ips=frozenset(),
    browser_dir_name='agent',
    product_names={'vanced': 'AntiVKGroupVanced', 'extended': 'AntiVKGroupExtended'},
)

__all__ = ["CFG", "BrandConfig"]
