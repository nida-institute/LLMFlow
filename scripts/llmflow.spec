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
        'llmflow.plugins.coverage_validator',
        'llmflow.plugins.echo',
        'llmflow.plugins.insert_references',
        'llmflow.plugins.xml_entry_to_base_json',
        'llmflow.plugins.xpath',
        'llmflow.plugins.xslt_transform',
        'llmflow.plugins.tsv_reader',
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
    [],
    exclude_binaries=True,
    name='llmflow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='llmflow',
)
