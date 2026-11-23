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
  test_core_wiring.py   runs the real scan for all 10 brands x 2 profiles
tools/
  check_core_detect_calls.py  bind every core -> detect call to its signature
  check_detect_constants.py   every det.CONST exists in all 10 brands
  check_finding_coverage.py   every emitted finding has a removal handler
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

## Build

```bash
pip install -e ".[dev]"
python build_all.py --clean         # all 10 brands -> dist/<brand>-vanced.exe
python build_all.py baidu qq        # selected brands only
python build_all.py --extended      # EXTENDED edition entry points
python verify_build.py              # smoke-test every EXE in dist/
python verify_build.py --skip-gui   # CLI checks only (faster)
```

Prebuilt binaries: [releases](https://github.com/retvil/antivancedcore/releases).

### Editions

One codebase, two entry points per brand:

- **VANCED** (`main.py`) — the brand's browser and search hijack vectors.
- **EXTENDED** (`main_extended.py`) — everything VANCED does, plus the brand's
  bundled products (mail clients, cloud drives, stores, local data dirs).

Both editions share the core; only the scan scope and product name differ.

### Unified multi-brand EXE

`main_multi.py` bundles **all 10 brands into a single EXE** with a runtime
brand picker — the user picks which vendor to find and remove, no separate
download per brand.

```
antivancedcore.exe                     # GUI: brand picker at the top
antivancedcore.exe --brand baidu --scan-only
antivancedcore.exe --brand mailru --scan-only --profile extended
antivancedcore.exe --list-engines
```

Build it with `python build_all.py --multi` -> `dist/antivancedcore.exe`.
