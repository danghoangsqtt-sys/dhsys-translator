import json
from fnmatch import fnmatch
from pathlib import Path

import pytest

from videotrans.configure._app_params import AppParams


def test_fresh_main_workflow_defaults_to_existing_hard_subtitle_enum(tmp_path):
    params = AppParams(_json_path=str(tmp_path / "fresh-params.json"))

    assert params.subtitle_type == 1


@pytest.mark.parametrize("saved_value", [0, 1, 2, 3, 4])
def test_legacy_subtitle_enum_values_are_preserved(tmp_path, saved_value):
    config_path = tmp_path / "params.json"
    config_path.write_text(json.dumps({"subtitle_type": saved_value}), encoding="utf-8")

    params = AppParams(_json_path=str(config_path))

    assert params.subtitle_type == saved_value


@pytest.mark.parametrize("invalid_value", [-1, 5, "2", None])
def test_invalid_legacy_subtitle_value_uses_fresh_hard_default(tmp_path, invalid_value):
    config_path = tmp_path / "params.json"
    config_path.write_text(json.dumps({"subtitle_type": invalid_value}), encoding="utf-8")

    params = AppParams(_json_path=str(config_path))

    assert params.subtitle_type == 1


@pytest.mark.parametrize("saved", [{}, {"f5tts_role": None, "is_cuda": "yes"}, []])
def test_legacy_params_use_defaults_for_missing_or_invalid_fields(tmp_path, saved):
    config_path = tmp_path / "params.json"
    config_path.write_text(json.dumps(saved), encoding="utf-8")

    params = AppParams(_json_path=str(config_path))

    assert params.f5tts_role.startswith("zh_female_nverguo.wav")
    assert params.is_cuda is False


def test_legacy_params_keep_valid_values_and_custom_f5_roles(tmp_path):
    config_path = tmp_path / "params.json"
    config_path.write_text(json.dumps({
        "output_dir": "custom-output",
        "is_cuda": True,
        "f5tts_role": "custom.wav#Hello\ncustom.wav#Hello",
        "future_setting": "preserved",
    }), encoding="utf-8")

    params = AppParams(_json_path=str(config_path))

    assert params.output_dir == "custom-output"
    assert params.is_cuda is True
    assert params.f5tts_role.splitlines()[0] == "custom.wav#Hello"
    assert params.f5tts_role.count("custom.wav#Hello") == 1
    assert "zh_female_nverguo.wav" in params.f5tts_role
    assert params.future_setting == "preserved"


def test_dockerignore_excludes_local_credentials():
    rules = [line for line in Path(".dockerignore").read_text(encoding="utf-8").splitlines()
             if line and not line.startswith("#")]
    for path in (
        "videotrans/params.json",
        "videotrans/cfg.json",
        ".env",
        ".env.production",
        "private/api.key",
        "private/ca.pem",
        "videotrans/output/clip.mp4",
    ):
        assert any(fnmatch(path, rule) for rule in rules), path
    assert not any(fnmatch("videotrans/configure/_app_params.py", rule) for rule in rules)
