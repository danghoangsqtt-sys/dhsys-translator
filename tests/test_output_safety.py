from pathlib import Path
from types import SimpleNamespace
import time

import pytest

from videotrans.configure import config
from videotrans.task._base import BaseTask
from videotrans.task._stage_assemble import AssembleMixin, _unused_video_path
from videotrans.task.trans_create import _clear_managed_cache
from webui import _new_output_dir


def test_clear_cache_only_removes_one_managed_task(tmp_path, monkeypatch):
    temp_root = tmp_path / "app-temp"
    task_cache = temp_root / "task-a"
    other_cache = temp_root / "task-b"
    task_cache.mkdir(parents=True)
    other_cache.mkdir()
    (task_cache / "intermediate.wav").write_bytes(b"audio")
    output = tmp_path / "output"
    output.mkdir()
    (output / "completed.mp4").write_bytes(b"video")
    monkeypatch.setattr(config, "TEMP_DIR", str(temp_root))

    _clear_managed_cache(task_cache)

    assert not task_cache.exists()
    assert other_cache.exists()
    assert (output / "completed.mp4").exists()


def test_clear_cache_refuses_output_path_and_root(tmp_path, monkeypatch):
    temp_root = tmp_path / "app-temp"
    temp_root.mkdir()
    output = tmp_path / "output"
    output.mkdir()
    (output / "completed.mp4").write_bytes(b"video")
    monkeypatch.setattr(config, "TEMP_DIR", str(temp_root))

    with pytest.raises(ValueError, match="Refusing"):
        _clear_managed_cache(output)
    with pytest.raises(ValueError, match="Refusing"):
        _clear_managed_cache(temp_root)
    assert (output / "completed.mp4").exists()


def test_set_end_never_removes_cache_outside_managed_root(tmp_path, monkeypatch):
    temp_root = tmp_path / "app-temp"
    temp_root.mkdir()
    outside = tmp_path / "user-output"
    outside.mkdir()
    saved = outside / "completed.mp4"
    saved.write_bytes(b"keep")
    monkeypatch.setattr(config, "TEMP_DIR", str(temp_root))
    monkeypatch.setattr(config.app_cfg, "exec_mode", "cli")
    monkeypatch.setattr(config.app_cfg, "stoped_uuid_set", set())

    task = object.__new__(BaseTask)
    task.cfg = SimpleNamespace(cache_folder=str(outside), target_dir=str(outside), name="clip", basename="clip.mp4")
    task.uuid = "outside-cache-test"
    task.signal = lambda **kwargs: None

    task.set_end(succeed=True)

    assert saved.read_bytes() == b"keep"


def test_set_end_removes_only_managed_cache(tmp_path, monkeypatch):
    temp_root = tmp_path / "app-temp"
    cache = temp_root / "task-1"
    cache.mkdir(parents=True)
    (cache / "intermediate.wav").write_bytes(b"scratch")
    other = temp_root / "task-2"
    other.mkdir()
    monkeypatch.setattr(config, "TEMP_DIR", str(temp_root))
    monkeypatch.setattr(config.app_cfg, "exec_mode", "cli")
    monkeypatch.setattr(config.app_cfg, "stoped_uuid_set", set())

    task = object.__new__(BaseTask)
    task.cfg = SimpleNamespace(cache_folder=str(cache), target_dir=str(tmp_path), name="clip", basename="clip.mp4")
    task.uuid = "inside-cache-test"
    task.signal = lambda **kwargs: None

    task.set_end(succeed=True)

    assert not cache.exists()
    assert other.exists()


def test_set_end_respects_keep_cache_option(tmp_path, monkeypatch):
    temp_root = tmp_path / "app-temp"
    cache = temp_root / "task-1"
    cache.mkdir(parents=True)
    saved = cache / "intermediate.wav"
    saved.write_bytes(b"keep")
    monkeypatch.setattr(config, "TEMP_DIR", str(temp_root))
    monkeypatch.setattr(config.app_cfg, "exec_mode", "cli")
    monkeypatch.setattr(config.app_cfg, "stoped_uuid_set", set())

    task = object.__new__(BaseTask)
    task.cfg = SimpleNamespace(cache_folder=str(cache), target_dir=str(tmp_path), name="clip",
                               basename="clip.mp4", clear_cache=False)
    task.uuid = "keep-cache-test"
    task.signal = lambda **kwargs: None

    task.set_end(succeed=True)

    assert saved.read_bytes() == b"keep"


def test_clear_cache_refuses_symlinked_parent(tmp_path, monkeypatch):
    temp_root = tmp_path / "app-temp"
    actual = temp_root / "actual"
    task_cache = actual / "task"
    task_cache.mkdir(parents=True)
    (task_cache / "intermediate.wav").write_bytes(b"scratch")
    link = temp_root / "link"
    try:
        link.symlink_to(actual, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Creating directory symlinks is unavailable")
    monkeypatch.setattr(config, "TEMP_DIR", str(temp_root))

    with pytest.raises(ValueError, match="symlinked"):
        _clear_managed_cache(link / "task")
    assert (task_cache / "intermediate.wav").exists()


def test_new_webui_run_preserves_previous_output(tmp_path):
    first = _new_output_dir(tmp_path, "video")
    previous = first / "completed.mp4"
    previous.write_bytes(b"old")

    second = _new_output_dir(tmp_path, "video")

    assert first != second
    assert previous.read_bytes() == b"old"


def test_only_video_export_chooses_unused_name(tmp_path):
    previous = tmp_path / "video.mp4"
    previous.write_bytes(b"old")
    (tmp_path / "video-2.mp4").write_bytes(b"other")

    assert _unused_video_path(previous) == tmp_path / "video-3.mp4"


def test_only_video_export_preserves_other_output(tmp_path):
    work = tmp_path / "task"
    work.mkdir()
    video = work / "video.mp4"
    video.write_bytes(b"new")
    subtitle = work / "subtitle.srt"
    subtitle.write_text("keep", encoding="utf-8")
    previous = tmp_path / "video.mp4"
    previous.write_bytes(b"old")
    cfg = SimpleNamespace(
        app_mode="biaozhun", only_out_mp4=True, targetdir_mp4=str(video),
        target_dir=str(work), name="video", basename="video.mp4",
    )
    task = type("Task", (AssembleMixin,), {
        "cfg": cfg, "precent": 1, "is_audio_trans": False, "cost_duration": time.time(),
        "_exit": lambda self: False, "set_end": lambda self, succeed: None,
    })()

    task.task_done()

    assert previous.read_bytes() == b"old"
    assert (tmp_path / "video-2.mp4").read_bytes() == b"new"
    assert subtitle.read_text(encoding="utf-8") == "keep"
