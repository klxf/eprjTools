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
    datas=[('icon.ico', '.')],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    console=False,
    name=f'eprjTools v{version}',
    icon=['icon.ico'],
    version='version.txt',
)
