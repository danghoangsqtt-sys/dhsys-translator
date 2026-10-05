import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from videotrans.mainwin import _actions_task
from videotrans.task._stage_subtitle import SubtitleMixin
from videotrans.task.subtitle_output import (
    SUBTITLE_TYPE_KEYS,
    build_output_receipt,
)


def _write_srt(path: Path, text: str) -> None:
    path.write_text(
        f"1\n00:00:00,000 --> 00:00:01,500\n{text}\n",
        encoding="utf-8",
    )


def test_persisted_enum_mapping_is_frozen():
    assert SUBTITLE_TYPE_KEYS == (
        "nosubtitle",
        "embedsubtitle",
        "softsubtitle",
        "embedsubtitle2",
        "softsubtitle2",
    )


@pytest.mark.parametrize(
    ("locale", "expected"),
    [
        (
            "en_US",
            [
                "No subtitles in the video",
                "Always visible on the video",
                "Turn on/off in the video player",
                "Always visible bilingual subtitles",
                "Bilingual subtitles: turn on/off in the player",
            ],
        ),
        (
            "vi_VN",
            [
                "Video không có phụ đề",
                "Luôn hiện chữ trên video",
                "Bật/tắt phụ đề trong trình phát",
                "Luôn hiện phụ đề song ngữ",
                "Phụ đề song ngữ: bật/tắt trong trình phát",
            ],
        ),
    ],
)
def test_subtitle_choices_describe_visible_results(locale, expected):
    catalog = json.loads(
        Path(f"videotrans/language/{locale}.json").read_text(encoding="utf-8")
    )

    assert [catalog[key] for key in SUBTITLE_TYPE_KEYS] == expected


@pytest.mark.parametrize("subtitle_type", [3, 4])
@pytest.mark.parametrize(
    ("output_srt", "expected_lines"),
    [
        (1, ["Original line", "Translated line"]),
        (2, ["Translated line", "Original line"]),
    ],
)
def test_bilingual_modes_preserve_source_target_order(
    tmp_path, monkeypatch, subtitle_type, output_srt, expected_lines
):
    source = tmp_path / "source.srt"
    target = tmp_path / "target.srt"
    cache = tmp_path / "cache"
    output = tmp_path / "output"
    cache.mkdir()
    output.mkdir()
    _write_srt(source, "Original line")
    _write_srt(target, "Translated line")

    processor = SimpleNamespace(
        cfg=SimpleNamespace(
            subtitle_type=subtitle_type,
            output_srt=output_srt,
            source_sub=str(source),
            target_sub=str(target),
            source_language_code="en",
            target_language_code="vi",
            target_language="Vietnamese",
            cache_folder=str(cache),
            target_dir=str(output),
        ),
    )
    processor._get_join_flag = SubtitleMixin._get_join_flag.__get__(processor)
    monkeypatch.setattr(
        "videotrans.task._stage_subtitle.set_ass_font", lambda path: path
    )

    SubtitleMixin._process_subtitles(processor)

    bilingual = (output / "shuang.srt").read_text(encoding="utf-8")
    visible_lines = [
        line for line in bilingual.splitlines()
        if line in {"Original line", "Translated line"}
    ]
    assert visible_lines == expected_lines


def test_output_receipt_reports_mode_paths_and_soft_player_requirement(tmp_path, monkeypatch):
    video = tmp_path / "translated.mp4"
    source = tmp_path / "en.srt"
    target = tmp_path / "vi.srt"
    for path in (video, source, target):
        path.write_text("fixture", encoding="utf-8")
    cfg = SimpleNamespace(
        subtitle_type=2,
        output_srt=0,
        targetdir_mp4=str(video),
        source_sub=str(source),
        target_sub=str(target),
        target_dir=str(tmp_path),
    )

    receipt = build_output_receipt(cfg)
    translations = {
        "output_receipt_title": "Output receipt",
        "subtitle_type_label": "Subtitle mode",
        "softsubtitle": "Turn on/off in the video player",
        "output_video_path": "Video file",
        "output_subtitle_paths": "Subtitle files",
        "soft_subtitle_player_instruction": "Enable the subtitle track in your player.",
    }
    monkeypatch.setattr(
        _actions_task,
        "tr",
        lambda key, *args: translations.get(key, key),
    )

    text = _actions_task.format_output_receipt(receipt)

    assert receipt["subtitle_type"] == 2
    assert receipt["video_path"] == str(video)
    assert receipt["subtitle_paths"] == [str(source), str(target)]
    assert "Turn on/off in the video player" in text
    assert str(video) in text
    assert str(source) in text and str(target) in text
    assert "Enable the subtitle track in your player." in text
