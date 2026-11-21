# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['brands\\ant2345\\main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['antivancedcore', 'antivancedcore.brand', 'antivancedcore.backup', 'antivancedcore.products_detect', 'antivancedcore.profiles', 'antivancedcore.policies', 'antivancedcore.engines', 'antivancedcore.exclusions', 'antivancedcore.report', 'antivancedcore.restore', 'antivancedcore.translations', 'antivancedcore.updater', 'antivancedcore.watchdog', 'tkinter', 'ttkbootstrap', 'psutil', 'brands.ant2345', 'brands.ant2345.ant2345_detect'],
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
    name='ant2345-vanced',
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
