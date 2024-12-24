# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['scoringhero.py'],
    pathex=['./.venv/Lib/site-packages'],
    binaries=[],
    datas=[('./.venv/Lib/site-packages/mne', 'mne'), ('./help/images/selection_box.png', 'help/images'), ('./themes/light_theme.qss', 'themes')],
    hiddenimports=['decorator'],
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
    name='scoringhero',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
