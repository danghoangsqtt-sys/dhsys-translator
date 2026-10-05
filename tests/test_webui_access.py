import os
import time

import pytest
from pathlib import Path

from webui import _collect_artifacts, _webui_auth


def test_webui_uses_supported_shared_ui_locale():
    import webui

    assert webui.WEBUI_LOCALE in {"vi_VN", "en_US"}


@pytest.mark.parametrize('source,target', [('en', 'zh-cn'), ('English', 'Simplified Chinese')])
def test_saved_languages_build_valid_ui_and_voice_roles(monkeypatch, source, target):
    import warnings
    import webui

    selected_locales = []
    monkeypatch.setattr(webui, '_user_params', {
        'source_language': source, 'target_language': target,
        'tts_type': 0, 'voice_role': 'test-role',
    })

    def roles(_tts_type, langcode=None):
        selected_locales.append(langcode)
        return ['No', 'test-role']

    monkeypatch.setattr(webui, 'role_menu', roles)
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter('always')
        app = webui.build_ui()

    controls = {component['props'].get('label'): component['props']
                for component in app.config['components']
                if component['props'].get('label') in ('Source Language', 'Target Language', 'Voice Role')}
    assert controls['Source Language']['value'] == 'English'
    assert controls['Target Language']['value'] == 'Simplified Chinese'
    assert controls['Voice Role']['value'] == 'test-role'
    assert 'zh-cn' in selected_locales
    assert not [w for w in recorded if 'not in the list of choices' in str(w.message)]


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1", "[::1]"])
def test_loopback_requires_no_authentication(host):
    assert _webui_auth(host, False) is None


@pytest.mark.parametrize("host,share", [("0.0.0.0", False), ("192.168.1.10", False), ("example.com", False), ("127.0.0.1", True)])
def test_network_or_share_requires_authentication(host, share):
    with pytest.raises(ValueError, match="requires"):
        _webui_auth(host, share)
    assert _webui_auth(host, share, "user", "password") == ("user", "password")


def test_partial_credentials_are_rejected():
    with pytest.raises(ValueError, match="both"):
        _webui_auth("127.0.0.1", False, "user", "")


def test_docker_entry_point_requires_runtime_credentials():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert 'CMD ["python", "webui.py", "--host", "0.0.0.0", "--port", "7860"]' in dockerfile
    assert _webui_auth("0.0.0.0", False, "admin", "sample-password") == ("admin", "sample-password")


def test_collect_artifacts_excludes_old_logs_and_config(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    old_video = output / "old.mp4"
    old_video.write_bytes(b"old")
    os.utime(old_video, (1, 1))
    started_at = time.time() - 1
    video = output / "new.mp4"
    video.write_bytes(b"video")
    subtitle = output / "new.srt"
    subtitle.write_text("subtitle", encoding="utf-8")
    (output / "app.log").write_text("secret", encoding="utf-8")
    (output / "params.json").write_text("secret", encoding="utf-8")

    preview, files = _collect_artifacts(output, started_at)

    assert preview == str(video)
    assert files == [str(subtitle)]


def test_collect_artifacts_rejects_symlink_outside_output(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    outside = tmp_path / "outside.srt"
    outside.write_text("secret", encoding="utf-8")
    link = output / "link.srt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("Creating symlinks is unavailable on this machine")

    assert _collect_artifacts(output, 0) == (None, [])
