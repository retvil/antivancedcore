# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_multi.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['antivancedcore', 'antivancedcore.brand', 'antivancedcore.backup', 'antivancedcore.products_detect', 'antivancedcore.profiles', 'antivancedcore.policies', 'antivancedcore.engines', 'antivancedcore.exclusions', 'antivancedcore.report', 'antivancedcore.restore', 'antivancedcore.translations', 'antivancedcore.updater', 'antivancedcore.watchdog', 'antivancedcore.cli', 'antivancedcore.app', 'tkinter', 'ttkbootstrap', 'psutil', 'brands.baidu', 'brands.baidu.baidu_detect', 'brands.baidu.brand_config', 'brands.sogou', 'brands.sogou.sogou_detect', 'brands.sogou.brand_config', 'brands.ant2345', 'brands.ant2345.ant2345_detect', 'brands.ant2345.brand_config', 'brands.ucweb', 'brands.ucweb.ucweb_detect', 'brands.ucweb.brand_config', 'brands.naver', 'brands.naver.naver_detect', 'brands.naver.brand_config', 'brands.kakao', 'brands.kakao.kakao_detect', 'brands.kakao.brand_config', 'brands.qq', 'brands.qq.qq_detect', 'brands.qq.brand_config', 'brands.wechat', 'brands.wechat.wechat_detect', 'brands.wechat.brand_config', 'brands.tencent', 'brands.tencent.tencent_detect', 'brands.tencent.brand_config', 'brands.mailru', 'brands.mailru.mailru_detect', 'brands.mailru.brand_config'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='antivancedcore',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
