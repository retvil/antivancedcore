"""BrandConfig for Kakao (brands/kakao/)."""

from antivancedcore.brand import BrandConfig

CFG = BrandConfig(
    name='Kakao',
    detect_module='kakao_detect',
    repo='retvil/AntiKakaoVanced',
    appdata_dir='AntiKakaoVanced',
    app_version="1.4.0",
    app_author="Nod33Eset",
    kill_names=('kakaotalk.exe', 'kakaomap.exe'),
    browser_process_marker='kakao',
    consent_prefixes=('Roaming: ', 'Local data: ', 'DNS: ', 'Extension: ', 'Cookies: ', 'Defender exclusion: '),
    policy_vendor_key='SOFTWARE\\Policies\\Kakao\\Kakao',
    policy_domain='kakao.com',
    remove_func_name="remove_kakao_search_policies",
    task_name='\\AntiKakao\\PolicyWatch',
    product_markers=('kakao', 'kakaotalk.exe', 'kakaomap.exe'),
    appx_match_pattern='kakao|카카오',
    dns_ips=frozenset(),
    browser_dir_name='kakaotalk',
    product_names={'vanced': 'AntiKakaoVanced', 'extended': 'AntiKakaoExtended'},
)

__all__ = ["CFG", "BrandConfig"]
