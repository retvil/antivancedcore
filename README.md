# AntiVancedCore

Single source of truth for the **Anti\<Brand\>Vanced** family — one shared core
(`antivancedcore/`) plus one thin per-brand wrapper under `brands/`.

Removes a vendor's browser/search hijack vectors and hard-locks the default
search engine via Windows enterprise policies. Previously this lived as 10
separate GitHub forks; development now happens only here.

## Layout

```
antivancedcore/        brand-agnostic core (engines, policies, backup,
                       exclusions, restore, updater, watchdog,
                       products_detect, profiles, report, cli, app,
                       translations — driven by BrandConfig)
brands/
  baidu/  sogou/  ant2345/  ucweb/  naver/
  kakao/  qq/     wechat/   tencent/  mailru/
    <brand>_detect.py   the brand's scan/remove engine
    brand_config.py     CFG = BrandConfig(...) with all brand constants
    main.py             VANCED edition entry point
    main_extended.py    EXTENDED edition entry point
tests/
  test_brand.py         validates every brand's CFG + detect wiring
  test_i18n.py          translation-key parity across 10 languages
```

## How it works

- Every brand ships a `BrandConfig` (in `brands/<name>/brand_config.py`) that
  carries all brand-specific values: GitHub repo, `%APPDATA%` dir, process
  kill-list, policy registry key + domain, watchdog task name, product markers,
  Appx/DNS patterns, consent prefixes, and product names.
- The core modules read **only** from that `BrandConfig`; the sole
  brand-specific code left out of the core is the `<brand>_detect.py` engine.
- `main.py` / `main_extended.py` call `app.run(CFG, "vanced"|"extended")`
  (GUI) or `cli.main(CFG, argv)` (non-interactive / Intune).

## Brands

| dir | detect module | GitHub repo (archived) |
|---|---|---|
| baidu | `baidu_detect` | retvil/AntiBaiduVanced |
| sogou | `sogou_detect` | retvil/AntiSogouVanced |
| ant2345 | `ant2345_detect` | retvil/Anti2345Vanced |
| ucweb | `ucweb_detect` | retvil/AntiUCWebVanced |
| naver | `naver_detect` | retvil/AntiNaverVanced |
| kakao | `kakao_detect` | retvil/AntiKakaoVanced |
| qq | `qq_detect` | retvil/AntiQQVanced |
| wechat | `wechat_detect` | retvil/AntiWeChatVanced |
| tencent | `tencent_detect` | retvil/AntiTencentVideoVanced |
| mailru | `mailru_detect` | retvil/AntiVKGroupVanced |

## Run

```bash
python -m pytest tests/ -q          # 4 tests: i18n parity + brand wiring
python brands/baidu/main.py         # GUI (VANCED)
python brands/baidu/main.py --help  # CLI
```
