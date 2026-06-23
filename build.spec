# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for SnapFlow."""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
project_root = Path(SPECPATH)

# Collect ALL customtkinter data files — this is what was missing
datas = collect_data_files("customtkinter", include_py_files=True)

hiddenimports = (
    collect_submodules("customtkinter")
    + collect_submodules("snapflow")
    + [
        "pystray",
        "pystray._win32",
        "PIL._tkinter_finder",
        "PIL.Image",
        "PIL.ImageDraw",
        "keyboard",
        "mss",
        "mss.windows",
        "pyperclip",
        "requests",
        "tkinter",
        "tkinter.ttk",
        "_tkinter",
    ]
)

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude server-side stuff from the desktop build
        "fastapi",
        "uvicorn",
        "openai",
        "pyinstaller",
    ],
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
    name="SnapFlow",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="SnapFlow.app",
        icon=None,
        bundle_identifier="com.snapflow.app",
    )
