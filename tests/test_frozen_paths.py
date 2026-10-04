import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from videotrans.configure import _paths
from videotrans.configure._paths import _frozen_roots, _prepare_frozen_home


def test_frozen_roots_keep_resources_separate_from_user_data(tmp_path):
    install = tmp_path / "Read Only Install"
    bundled = install / "_internal"
    local_data = tmp_path / "user" / "AppData" / "Local"

    resources, data, legacy = _frozen_roots(
        install / "sp.exe", bundled, local_data, tmp_path / "user", "win32"
    )

    assert resources == bundled.resolve()
    assert data == (local_data / "pyVideoTrans").resolve()
    assert legacy == install
    assert not data.is_relative_to(legacy)


def test_frozen_home_copies_assets_and_legacy_config_without_overwrite(tmp_path):
    install = tmp_path / "install"
    resources = install / "_internal"
    data = tmp_path / "userdata"
    language = resources / "videotrans" / "language" / "en_US.json"
    language.parent.mkdir(parents=True)
    language.write_text('{"test":"from bundle"}', encoding="utf-8")
    old_config = install / "videotrans" / "params.json"
    old_config.parent.mkdir(parents=True)
    old_config.write_text('{"api_key":"legacy"}', encoding="utf-8")

    _prepare_frozen_home(resources, data, install)

    copied_config = data / "videotrans" / "params.json"
    copied_language = data / "videotrans" / "language" / "en_US.json"
    assert copied_config.read_text(encoding="utf-8") == old_config.read_text(encoding="utf-8")
    assert copied_language.read_text(encoding="utf-8") == language.read_text(encoding="utf-8")
    copied_config.write_text('{"api_key":"user updated"}', encoding="utf-8")
    _prepare_frozen_home(resources, data, install)
    assert copied_config.read_text(encoding="utf-8") == '{"api_key":"user updated"}'


def test_resource_path_does_not_depend_on_working_directory(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    asset = bundle / "videotrans" / "styles" / "style.qss"
    asset.parent.mkdir(parents=True)
    asset.write_text("QWidget {}", encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.setattr(_paths, "RESOURCE_ROOT", str(bundle))
    monkeypatch.chdir(elsewhere)

    assert _paths.resource_path("videotrans", "styles", "style.qss").read_text(encoding="utf-8") == "QWidget {}"


def test_frozen_home_creates_config_directory_when_bundle_has_no_assets(tmp_path):
    data = tmp_path / "userdata"

    _prepare_frozen_home(tmp_path / "empty_bundle", data, tmp_path / "install")

    assert (data / "videotrans").is_dir()


def test_frozen_home_never_overwrites_an_existing_icon(tmp_path):
    resources = tmp_path / "bundle"
    data = tmp_path / "userdata"
    bundled_icon = resources / "videotrans" / "styles" / "icon.ico"
    bundled_icon.parent.mkdir(parents=True)
    bundled_icon.write_bytes(b"bundled icon")
    existing_icon = data / "videotrans" / "styles" / "icon.ico"
    existing_icon.parent.mkdir(parents=True)
    existing_icon.write_bytes(b"in use icon")

    _prepare_frozen_home(resources, data, tmp_path / "install")

    assert existing_icon.read_bytes() == b"in use icon"


def test_frozen_home_concurrent_seed_has_one_writer_and_no_errors(tmp_path):
    resources = tmp_path / "bundle"
    data = tmp_path / "userdata"
    bundled_language = resources / "videotrans" / "language" / "en_US.json"
    bundled_language.parent.mkdir(parents=True)
    bundled_language.write_text('{"seed":"bundle"}', encoding="utf-8")

    with ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(
            lambda _: _prepare_frozen_home(resources, data, tmp_path / "install"),
            range(12),
        ))

    copied_language = data / "videotrans" / "language" / "en_US.json"
    assert copied_language.read_text(encoding="utf-8") == '{"seed":"bundle"}'


def test_frozen_config_import_writes_only_to_user_data_from_other_cwd(tmp_path):
    install = tmp_path / "Read Only Install"
    bundle = install / "_internal"
    language = bundle / "videotrans" / "language" / "en_US.json"
    language.parent.mkdir(parents=True)
    language.write_text("{}", encoding="utf-8")
    executable = install / "sp.exe"
    executable.write_bytes(b"placeholder")
    before = {path.relative_to(install) for path in install.rglob('*')}
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    data_base = tmp_path / "user-local-data"
    script = (
        "import json, os, sys; "
        "sys.frozen = True; "
        "sys._MEIPASS = os.environ['TEST_BUNDLE']; "
        "sys.executable = os.environ['TEST_EXE']; "
        "from videotrans.configure import config; "
        "print(json.dumps({'root': config.ROOT_DIR, 'logs': config.LOGS_DIR}))"
    )
    env = dict(os.environ, LOCALAPPDATA=str(data_base), TEST_BUNDLE=str(bundle),
               TEST_EXE=str(executable), PYTHONPATH=str(Path(__file__).resolve().parents[1]))

    result = subprocess.run([sys.executable, "-c", script], cwd=elsewhere, env=env,
                            capture_output=True, text=True, timeout=30)

    assert result.returncode == 0, result.stderr
    paths = json.loads(result.stdout.splitlines()[-1])
    assert Path(paths["root"]) == data_base / "pyVideoTrans"
    assert Path(paths["logs"]).is_dir()
    assert {path.relative_to(install) for path in install.rglob('*')} == before
