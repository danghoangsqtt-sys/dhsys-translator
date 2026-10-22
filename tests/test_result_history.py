import json

from videotrans.ui import result_history
from videotrans.ui.result_history import (
    MAX_ENTRIES,
    append_results,
    load_history,
    recent_results,
)


def _receipt(tmp_path, name, create=True):
    video = tmp_path / f"{name}.mp4"
    if create:
        video.write_bytes(b"0")
    return {"video_path": str(video), "subtitle_type": 1, "target_language_code": "vi", "api_key": "secret"}


def test_append_keeps_newest_first_and_dedupes(tmp_path):
    path = tmp_path / "history.json"
    append_results([_receipt(tmp_path, "a")], path)
    append_results([_receipt(tmp_path, "b")], path)
    append_results([_receipt(tmp_path, "a")], path)

    names = [entry["video_path"].rsplit("\\", 1)[-1].rsplit("/", 1)[-1] for entry in load_history(path)]
    assert names == ["a.mp4", "b.mp4"]


def test_history_is_capped(tmp_path):
    path = tmp_path / "history.json"
    append_results([_receipt(tmp_path, f"v{i}") for i in range(MAX_ENTRIES + 5)], path)

    entries = load_history(path)
    assert len(entries) == MAX_ENTRIES
    assert entries[0]["video_path"].endswith(f"v{MAX_ENTRIES + 4}.mp4")


def test_only_file_and_language_fields_are_stored(tmp_path):
    path = tmp_path / "history.json"
    append_results([_receipt(tmp_path, "a")], path)

    entry = json.loads(path.read_text(encoding="utf-8"))[0]
    assert "api_key" not in entry
    assert entry["target_language_code"] == "vi"
    assert isinstance(entry["finished_at"], int)


def test_recent_results_drop_missing_videos(tmp_path):
    path = tmp_path / "history.json"
    append_results([_receipt(tmp_path, "kept"), _receipt(tmp_path, "gone", create=False)], path)

    assert [entry["video_path"] for entry in recent_results(path)] == [str(tmp_path / "kept.mp4")]
    assert len(load_history(path)) == 2


def test_corrupt_or_wrong_type_file_is_reset(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("{not json", encoding="utf-8")
    assert load_history(path) == []
    assert json.loads(path.read_text(encoding="utf-8")) == []

    path.write_text('{"video_path": "x"}', encoding="utf-8")
    assert load_history(path) == []


def test_failed_write_leaves_previous_file_and_no_temp(tmp_path, monkeypatch):
    path = tmp_path / "history.json"
    append_results([_receipt(tmp_path, "a")], path)
    before = path.read_text(encoding="utf-8")

    def broken_dump(*args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(result_history.json, "dump", broken_dump)
    try:
        append_results([_receipt(tmp_path, "b")], path)
    except RuntimeError:
        pass

    assert path.read_text(encoding="utf-8") == before
    assert [p.name for p in tmp_path.iterdir() if p.name.startswith(".result_history-")] == []
