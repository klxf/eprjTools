# -*- mode: python ; coding: utf-8 -*-
import re

def get_version():
    with open('version.txt', 'r') as f:
        content = f.read()
        match = re.search(r'FileVersion.*?(\d+\.\d+\.\d+)', content)
        if match:
            version = match.group(1)
        else:
            version = '0.0.0'
    return version

version = get_version()

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.ico', '.')],
    hiddenimports=[],
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
    name=f'eprjTools v{version}',
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
    icon=['icon.ico'],
    version='version.txt',
)
