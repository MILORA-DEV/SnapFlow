# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SnapFlow desktop application.
Generates a single standalone .exe with no console window.
"""
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

snapflow_dir = Path("snapflow")
snapflow_files = []
if snapflow_dir.exists():
    for py_file in snapflow_dir.rglob("*.py"):
        snapflow_files.append(str(py_file))

customtkinter_submodules = collect_submodules('customtkinter')
customtkinter_datas = collect_data_files('customtkinter')

a = Analysis(
    ["snapflow/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[
        *customtkinter_datas,
        ("snapflow/assets/icon.ico", "snapflow/assets"),
    ],
    hiddenimports=[
        "snapflow",
        "snapflow.core",
        "snapflow.core.actions",
        "snapflow.core.actions.base",
        "snapflow.core.actions.calendar",
        "snapflow.core.actions.code",
        "snapflow.core.actions.map_link",
        "snapflow.core.actions.markdown",
        "snapflow.core.connection",
        "snapflow.core.analyzer",
        "snapflow.core.license",
        "snapflow.ui",
        "snapflow.ui.app",
        "snapflow.ui.theme",
        "snapflow.ui.views",
        "snapflow.ui.views.dashboard",
        "snapflow.ui.views.history",
        "snapflow.ui.views.settings",
        "snapflow.ui.toast",
        "snapflow.ui.tray",
        "snapflow.ui.license_gate",
        *customtkinter_submodules,
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",
        "mss",
        "keyboard",
        "pystray",
        "requests",
        "dotenv",
        "certifi",
        "urllib3",
        "pyperclip",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "pytest",
        "setuptools",
        "distutils",
        "openai",
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="snapflow/assets/icon.ico",
)