# -*- coding: utf-8 -*-
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path



def _frozen_roots(executable, bundled_root=None, local_app_data=None, home=None, platform_name=None):
    """Return separate read-only bundle and writable user-data directories."""
    executable_dir = Path(executable).resolve().parent
    resource_dir = Path(bundled_root) if bundled_root else executable_dir / '_internal'
    platform_name = platform_name or sys.platform
    home = Path(home) if home else Path.home()
    if platform_name == 'win32':
        data_base = Path(local_app_data) if local_app_data else Path(os.environ.get('LOCALAPPDATA', home / 'AppData' / 'Local'))
        data_dir = data_base / 'pyVideoTrans'
    elif platform_name == 'darwin':
        data_dir = home / 'Library' / 'Application Support' / 'pyVideoTrans'
    else:
        data_base = Path(os.environ.get('XDG_DATA_HOME', home / '.local' / 'share'))
        data_dir = data_base / 'pyVideoTrans'
    return resource_dir.resolve(), data_dir.resolve(), executable_dir


def _copy_missing_frozen_asset(source, destination):
    """Seed an asset once without overwriting or racing another app instance."""
    if destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock_path = destination.with_name(f".{destination.name}.seed.lock")
    for _ in range(100):
        try:
            lock_descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except (FileExistsError, PermissionError):
            if destination.exists():
                return
            # Windows can report sharing contention on an existing O_EXCL
            # lock file as PermissionError instead of FileExistsError. Keep
            # the existing bounded retry behavior; a persistent permission
            # problem still times out and surfaces below.
            time.sleep(0.05)
            continue
        os.close(lock_descriptor)
        try:
            if destination.exists():
                return
            temporary_path = None
            try:
                with tempfile.NamedTemporaryFile(
                        dir=destination.parent,
                        prefix=f".{destination.name}.",
                        suffix=".tmp",
                        delete=False) as temporary_file:
                    temporary_path = Path(temporary_file.name)
                    with source.open("rb") as source_file:
                        shutil.copyfileobj(source_file, temporary_file)
                if not destination.exists():
                    os.replace(temporary_path, destination)
                    temporary_path = None
            finally:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)
        finally:
            lock_path.unlink(missing_ok=True)
        return
    if not destination.exists():
        raise RuntimeError(f"Timed out seeding frozen asset: {destination}")


def _prepare_frozen_home(resource_dir, data_dir, legacy_dir):
    """Copy missing bundled assets and legacy configuration without replacing user data."""
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / 'videotrans').mkdir(parents=True, exist_ok=True)
    for relative in ('videotrans/styles', 'videotrans/language',
                     'videotrans/voicejson', 'videotrans/prompts'):
        source_dir = resource_dir / relative
        if not source_dir.is_dir():
            continue
        for source in source_dir.rglob('*'):
            if source.is_file():
                destination = data_dir / source.relative_to(resource_dir)
                _copy_missing_frozen_asset(source, destination)
    for name in ('cfg.json', 'params.json'):
        source = legacy_dir / 'videotrans' / name
        destination = data_dir / 'videotrans' / name
        if source.is_file():
            _copy_missing_frozen_asset(source, destination)
    for name in ('languages.json',):
        source = legacy_dir / 'videotrans' / name
        destination = data_dir / 'videotrans' / name
        if source.is_file():
            _copy_missing_frozen_asset(source, destination)


IS_FROZEN = bool(getattr(sys, 'frozen', False))
SYS_TMP = Path(tempfile.gettempdir()).as_posix()
if IS_FROZEN:
    _resource_dir, _data_dir, _legacy_dir = _frozen_roots(sys.executable, getattr(sys, '_MEIPASS', None))
    RESOURCE_ROOT = _resource_dir.as_posix()
    ROOT_DIR = _data_dir.as_posix()
    LEGACY_ROOT_DIR = _legacy_dir.as_posix()
    _prepare_frozen_home(_resource_dir, _data_dir, _legacy_dir)
else:
    ROOT_DIR = Path(__file__).parent.parent.parent.as_posix()
    RESOURCE_ROOT = ROOT_DIR
    LEGACY_ROOT_DIR = ROOT_DIR


def resource_path(*parts):
    """Locate a bundled read-only asset independently of the process CWD."""
    return Path(RESOURCE_ROOT).joinpath(*parts)
TEMP_ROOT = f'{ROOT_DIR}/tmp'
LOGS_DIR = f'{ROOT_DIR}/logs'

TRANSLATE_CACHE = f'{TEMP_ROOT}/translate_cache'
DUBBING_CACHE = f'{TEMP_ROOT}/dubbing_cache'

# 单视频模式时重新进行配音，队列数据文件和停止标识文件
REDUBB_QUEUE_FILE=f'{TEMP_ROOT}/redubbing.json'
REDUBB_STATUS_FILE=f'{TEMP_ROOT}/stopredubbing.pid'

Path(f"{ROOT_DIR}/models").mkdir(parents=True, exist_ok=True)
Path(f"{ROOT_DIR}/logs").mkdir(parents=True, exist_ok=True)
Path(f"{TRANSLATE_CACHE}").mkdir(parents=True, exist_ok=True)
Path(f"{DUBBING_CACHE}").mkdir(parents=True, exist_ok=True)

def fix_ssl_cert_env():
    """Preserve explicit CA bundles and provide a default only when none is set."""
    keys = ('REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE', 'SSL_CERT_FILE')
    configured = {key: os.environ[key] for key in keys if os.environ.get(key)}
    for key, value in configured.items():
        if not Path(value).expanduser().is_file():
            raise FileNotFoundError(f'{key} points to a missing certificate bundle: {value}')

    if configured:
        default_bundle = next(iter(configured.values()))
    else:
        import certifi
        default_bundle = certifi.where()
        if not Path(default_bundle).is_file():
            raise FileNotFoundError(f'certifi certificate bundle is missing: {default_bundle}')
    for key in keys:
        if not os.environ.get(key):
            os.environ[key] = default_bundle



def _set_env():
    from videotrans.configure.constants import no_proxy
    if IS_FROZEN:
        os.environ['TQDM_DISABLE'] = '1'
    os.environ['no_proxy'] = no_proxy
    os.environ['NO_PROXY'] = no_proxy
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
    os.environ["CT2_VERBOSE"] = "1"
    os.environ["CT2_CUDA_ALLOW_BF16"] = "1"
    os.environ["CT2_CUDA_ALLOW_FP16"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["PYTHONWARNINGS"]="ignore"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    os.environ['PYTHONUTF8'] = '1'
    os.environ['QT_API'] = 'pyside6'
    os.environ['SOFT_NAME'] = 'pyvideotrans'
    os.environ['MODELSCOPE_CACHE'] = ROOT_DIR + "/models"
    os.environ['HF_HOME'] = ROOT_DIR + "/models"
    os.environ['PYANNOTE_CACHE'] = ROOT_DIR + "/models"
    os.environ['PKUSEG_HOME'] = ROOT_DIR + "/models/pkuser_home"
    os.environ['HF_HUB_CACHE'] = ROOT_DIR + "/models"
    os.environ['HF_TOKEN_PATH'] = ROOT_DIR + "/models/hf_token.txt"
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = 'true'
    os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = "120"
    os.environ['HF_HUB_ETAG_TIMEOUT'] = "120"
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ['GRADIO_ANALYTICS_ENABLED'] = '0'
    # 必须在 import requests, modelscope 等库之前执行！
    fix_ssl_cert_env()
    if Path(f'{ROOT_DIR}/netoffline.txt').is_file() or Path(f'{RESOURCE_ROOT}/netoffline.txt').is_file():
        os.environ['HF_HUB_OFFLINE'] = '1'

    if sys.platform == 'win32' and IS_FROZEN:
        os.environ['PATH'] = f'{RESOURCE_ROOT}/torch/lib;' + os.environ.get("PATH", "")
    os.environ['PATH'] = ROOT_DIR + os.pathsep + f'{RESOURCE_ROOT}/ffmpeg' + os.pathsep + f'{RESOURCE_ROOT}/ffmpeg/sox' + os.pathsep + os.environ.get(
        "PATH", "")
