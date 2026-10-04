# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for pyVideoTrans
# Windows candidate build. User models, cache, logs, and output stay outside the bundle.

import sys
# The dynamic provider/dialog set expands PyInstaller's module graph well
# beyond the default recursion depth on Windows.
sys.setrecursionlimit(20000)

from pathlib import Path

PROJECT_ROOT = Path.cwd()

# Collect data files
def collect_data_files():
    data_files = []

    # Styles (QSS, icons, fonts, logos)
    styles_dir = PROJECT_ROOT / "videotrans" / "styles"
    if styles_dir.exists():
        for f in styles_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(PROJECT_ROOT)
                data_files.append((str(f), str(rel.parent)))

    # UI dark theme resources
    dark_dir = PROJECT_ROOT / "videotrans" / "ui" / "dark"
    if dark_dir.exists():
        for f in dark_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(PROJECT_ROOT)
                data_files.append((str(f), str(rel.parent)))

    # Language JSON files
    lang_dir = PROJECT_ROOT / "videotrans" / "language"
    if lang_dir.exists():
        for f in lang_dir.rglob("*.json"):
            rel = f.relative_to(PROJECT_ROOT)
            data_files.append((str(f), str(rel.parent)))

    # Voice JSON configs
    voice_dir = PROJECT_ROOT / "videotrans" / "voicejson"
    if voice_dir.exists():
        for f in voice_dir.rglob("*.json"):
            rel = f.relative_to(PROJECT_ROOT)
            data_files.append((str(f), str(rel.parent)))
        for f in voice_dir.rglob("*.yaml"):
            rel = f.relative_to(PROJECT_ROOT)
            data_files.append((str(f), str(rel.parent)))

    # Prompts
    prompts_dir = PROJECT_ROOT / "videotrans" / "prompts"
    if prompts_dir.exists():
        for f in prompts_dir.rglob("*.txt"):
            rel = f.relative_to(PROJECT_ROOT)
            data_files.append((str(f), str(rel.parent)))

    # FunASR remote-code helper is loaded by filename at runtime.
    codes_dir = PROJECT_ROOT / "videotrans" / "codes"
    if codes_dir.exists():
        for f in codes_dir.glob("*.py"):
            rel = f.relative_to(PROJECT_ROOT)
            data_files.append((str(f), str(rel.parent)))

    # FFmpeg binaries (if present locally)
    ffmpeg_dir = PROJECT_ROOT / "ffmpeg"
    if ffmpeg_dir.exists():
        for f in ffmpeg_dir.rglob("*"):
            if f.is_file() and f.name != ".gitignore":
                rel = f.relative_to(PROJECT_ROOT)
                data_files.append((str(f), str(rel.parent)))

    return data_files

# Only essential hidden imports that PyInstaller might miss
hidden_imports = [
    # Project modules
    "videotrans",
    "videotrans.configure",
    "videotrans.task",
    "videotrans.recognition",
    "videotrans.translator",
    "videotrans.tts",
    "videotrans.util",
    "videotrans.mainwin",
    "videotrans.component",
    "videotrans.winform",
    "videotrans.process",
    "videotrans.codes",
    "videotrans.prompts",
    "videotrans.voicejson",
    "videotrans.language",
    "videotrans.styles",
    # PySide6 QtMultimedia for video preview
    "PySide6.QtMultimedia",
    "PySide6.QtNetwork",
    # Common ML libs that may need explicit import
    "ctranslate2",
    "onnxruntime",
    "faster_whisper",
    "whisper",
    "funasr",
    "modelscope",
    "edge_tts",
    "gtts",
]

# Providers and dialogs are resolved with importlib from runtime names.
# Include the smoke-tested paths explicitly. Packaging every source module makes
# PyInstaller's Windows graph recurse until the interpreter stack overflows.
hidden_imports += [
    "videotrans.recognition._faster_whisper",
    "videotrans.translator._google",
    "videotrans.tts._edgetts",
    "videotrans.winform.chatgpt",
]

# Exclude unnecessary modules to reduce size
excludes = [
    "tkinter",
    "IPython",
    "jupyter",
    "notebook",
    "pytest",
    "ruff",
    "mypy",
    "black",
    "isort",
    "flake8",
    "bandit",
    "sphinx",
    "docutils",
    "test",
    "tests",
    "unittest",
    "pdb",
    "idlelib",
    "pydoc",
    "lib2to3",
    "setuptools",
    "pip",
    "wheel",
]

block_cipher = None

a = Analysis(
    ["sp.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=collect_data_files(),
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Keep hook-provided package data. Broad name filters can remove required
# resources from dependencies, including files whose names contain "test".

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="sp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    exclude_binaries=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / "videotrans" / "styles" / "icon.ico"),
    version=str(PROJECT_ROOT / "version.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="sp",
)
