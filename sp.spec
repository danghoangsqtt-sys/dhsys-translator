# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for pyVideoTrans
# Windows candidate build. User models, cache, logs, and output stay outside the bundle.

import ast
import sys
# The dynamic provider/dialog set expands PyInstaller's module graph well
# beyond the default recursion depth on Windows.
sys.setrecursionlimit(20000)

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files as collect_package_data

PROJECT_ROOT = Path.cwd()


def menu_hidden_imports():
    """Bundle windows reached only through menu names passed to importlib."""
    menu_source = PROJECT_ROOT / "videotrans" / "ui" / "menu_list.py"
    tree = ast.parse(menu_source.read_text(encoding="utf-8"), filename=str(menu_source))
    menu_sections = {
        "MENU_CFG_PANEL", "MENU_CFG_TRANS", "MENU_CFG_TTS",
        "MENU_CFG_STT", "MENU_CFG_TOOLS", "MENU_CFG_HELP",
    }
    component_windows = {
        "clip_video", "realtime_stt", "textmatching", "set_ass",
        "formatsrtfiles", "xxl",
    }
    modules = set()
    for statement in tree.body:
        if not isinstance(statement, ast.Assign) or not isinstance(statement.value, ast.List):
            continue
        if not any(isinstance(target, ast.Name) and target.id in menu_sections
                   for target in statement.targets):
            continue
        for entry in statement.value.elts:
            if not isinstance(entry, ast.Tuple) or len(entry.elts) != 3:
                continue
            name, _, action = entry.elts
            if not (isinstance(name, ast.Constant) and isinstance(name.value, str)
                    and isinstance(action, ast.Constant) and action.value is None):
                continue
            if name.value in component_windows:
                modules.add(f"videotrans.component.{name.value}")
            else:
                modules.add(f"videotrans.winform.{name.value}")
                modules.add(f"videotrans.ui.{name.value}")
    if len(modules) < 5:
        raise RuntimeError(f"No dynamic GUI menu modules found in {menu_source}")
    return sorted(modules)

# Collect data files
def collect_data_files():
    data_files = []

    # faster-whisper resolves its Silero VAD model relative to utils.py.
    # PyInstaller bundles Python modules but does not include this ONNX asset.
    vad_assets = collect_package_data(
        "faster_whisper", includes=["assets/silero_vad_v6.onnx"]
    )
    if len(vad_assets) != 1:
        raise RuntimeError("Missing faster-whisper Silero VAD asset in build environment")
    data_files.extend(vad_assets)

    # zhconv loads this dictionary through pkg_resources when Chinese speech
    # recognition normalizes simplified/traditional text.
    zhconv_assets = collect_package_data("zhconv", includes=["zhcdict.json"])
    if len(zhconv_assets) != 1:
        raise RuntimeError("Missing zhconv dictionary in build environment")
    data_files.extend(zhconv_assets)

    license_file = PROJECT_ROOT / "LICENSE"
    if license_file.is_file():
        data_files.append((str(license_file), "."))

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
        for name in ("vi_VN.json", "en_US.json"):
            f = lang_dir / name
            if not f.is_file():
                continue
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
# Menu imports are derived from their declarations; collecting every source
# module caused a Windows interpreter stack overflow in an earlier build.
hidden_imports += [
    "videotrans.recognition._whisper",
    "videotrans.translator._google",
    "videotrans.translator._microsoft",
    "videotrans.tts._edgetts",
    "videotrans.winform.chatgpt",
    "videotrans.ui.chatgpt",
]
hidden_imports += menu_hidden_imports()

# Exclude unnecessary modules to reduce size
excludes = [
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
