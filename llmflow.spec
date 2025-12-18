# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/llmflow/cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('prompts', 'prompts'),
        ('templates', 'templates'),
    ],
    hiddenimports=[
        'llmflow',
        'llmflow.cli',
        'llmflow.runner',
        'llmflow.utils',
        'llmflow.modules',
        'llmflow.plugins',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['setuptools', 'distutils', 'pip', 'wheel'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='llmflow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
