import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QLabel

from videotrans import recognition, translator, tts
from videotrans.configure._i18n import tr
from videotrans.ui.wizard.adapter import CheckMirror, ComboMirror, MainWindowAdapter
from videotrans.ui.wizard.presets import (
    APP_MODE_EXTRACT,
    APP_MODE_STANDARD,
    PURPOSE_DUB_SUBTITLES,
    PURPOSE_SRT_ONLY,
    PURPOSE_SUBTITLES_ONLY,
    purpose_for,
    purpose_settings,
)

app = QApplication.instance() or QApplication([])


# ------------------------------------------------------------------ presets
def test_purpose_presets_map_to_existing_settings():
    dub = purpose_settings(PURPOSE_DUB_SUBTITLES, 2)
    subs = purpose_settings(PURPOSE_SUBTITLES_ONLY, 0)
    srt = purpose_settings(PURPOSE_SRT_ONLY, 3)

    assert (dub.app_mode, dub.dubbing, dub.subtitle_type, dub.needs_target_language) == (APP_MODE_STANDARD, True, 2, True)
    assert (subs.app_mode, subs.dubbing, subs.subtitle_type) == (APP_MODE_STANDARD, False, 1)
    assert (srt.app_mode, srt.dubbing, srt.subtitle_type, srt.needs_target_language) == (APP_MODE_EXTRACT, False, None, False)


def test_purpose_is_inferred_from_classic_settings():
    assert purpose_for(APP_MODE_EXTRACT, "vi-VN-HoaiMyNeural") == PURPOSE_SRT_ONLY
    assert purpose_for(APP_MODE_STANDARD, "No") == PURPOSE_SUBTITLES_ONLY
    assert purpose_for(APP_MODE_STANDARD, "vi-VN-HoaiMyNeural") == PURPOSE_DUB_SUBTITLES


# ------------------------------------------------------------------ mirrors
def test_combo_mirror_copies_items_hidden_rows_and_syncs_both_ways():
    source = QComboBox()
    source.setObjectName("translate_type")
    source.addItems(["A", "B", "C"])
    source.view().setRowHidden(1, True)
    source.setCurrentIndex(2)
    mirror = ComboMirror(source)

    assert [mirror.itemText(i) for i in range(mirror.count())] == ["A", "B", "C"]
    assert mirror.view().isRowHidden(1)
    assert mirror.currentIndex() == 2

    mirror.setCurrentIndex(0)
    assert source.currentIndex() == 0
    source.setCurrentIndex(2)
    assert mirror.currentIndex() == 2

    source.clear()
    source.addItems(["X", "Y"])
    source.setCurrentIndex(1)
    assert [mirror.itemText(i) for i in range(mirror.count())] == ["X", "Y"]
    assert mirror.currentIndex() == 1


def test_check_mirror_syncs_both_ways():
    source = QCheckBox("Slow video")
    mirror = CheckMirror(source)

    mirror.setChecked(True)
    assert source.isChecked()
    source.setChecked(False)
    assert not mirror.isChecked()
    assert mirror.text() == "Slow video"


# --------------------------------------------------------------- fake main
def _combo(name, items, index=0):
    combo = QComboBox()
    combo.setObjectName(name)
    combo.addItems(items)
    combo.setCurrentIndex(index)
    return combo


def _check(name):
    box = QCheckBox(name)
    box.setObjectName(name)
    return box


class _Action:
    def __init__(self, main):
        self.main = main
        self.queue_mp4 = []
        self.calls = []

    def set_tiquzimu(self):
        self.calls.append("tiqu")
        self.main.app_mode = APP_MODE_EXTRACT

    def set_biaozhun(self):
        self.calls.append("biaozhun")
        self.main.app_mode = APP_MODE_STANDARD

    def listen_voice_fun(self):
        self.calls.append("listen")


def _main(target_index=1, voice="No"):
    main = SimpleNamespace(
        app_mode=APP_MODE_STANDARD,
        target_dir=None,
        source_mp4=QLabel(),
        output_dir=QLabel(),
        source_language=_combo("source_language", ["English", "Tiếng Việt", "auto"]),
        target_language=_combo("target_language", ["-", "Tiếng Việt", "English"], target_index),
        voice_role=_combo("voice_role", ["No", "clone", "HoaiMy", "NamMinh"]),
        subtitle_type=_combo("subtitle_type", ["none", "hard", "soft", "hard2", "soft2"], 1),
        recogn_type=_combo("recogn_type", recognition.RECOGN_NAME_LIST),
        model_name=_combo("model_name", ["large-v3-turbo"]),
        translate_type=_combo("translate_type", translator.TRANSLASTE_NAME_LIST),
        tts_type=_combo("tts_type", tts.TTS_NAME_LIST),
        voice_autorate=_check("voice_autorate"),
        video_autorate=_check("video_autorate"),
        is_separate=_check("is_separate"),
        enable_cuda=_check("enable_cuda"),
        shown=[],
    )
    main.voice_role.setCurrentText(voice)
    main.win_action = _Action(main)
    main.show_workspace = lambda: main.shown.append("workspace")
    return main


# ------------------------------------------------------------------ adapter
def test_adapter_sets_videos_output_and_purposes():
    main = _main()
    adapter = MainWindowAdapter(main)

    adapter.set_videos(["D:/a.mp4", "D:/b.mkv"])
    assert main.win_action.queue_mp4 == ["D:/a.mp4", "D:/b.mkv"]
    assert main.source_mp4.text() == "2 videos"

    adapter.set_output_dir("D:/out")
    assert main.target_dir == "D:/out"

    adapter.apply_purpose(PURPOSE_DUB_SUBTITLES)
    assert main.voice_role.currentText() == "HoaiMy"
    assert main.app_mode == APP_MODE_STANDARD

    adapter.apply_purpose(PURPOSE_SUBTITLES_ONLY)
    assert main.voice_role.currentText() == "No"
    assert main.subtitle_type.currentIndex() == 1

    adapter.apply_purpose(PURPOSE_SRT_ONLY)
    assert main.win_action.calls[-1] == "tiqu"
    assert not adapter.needs_target_language()


def test_selected_providers_follow_dubbing_and_target():
    main = _main(target_index=0)
    adapter = MainWindowAdapter(main)
    assert [kind for kind, _ in adapter.selected_providers()] == ["recognition"]

    main.target_language.setCurrentIndex(1)
    main.voice_role.setCurrentText("HoaiMy")
    assert [kind for kind, _ in adapter.selected_providers()] == ["recognition", "translation", "tts"]


# ------------------------------------------------------------------- step 1
def _video_step(main, tmp_path, **kwargs):
    from videotrans.ui.wizard.step_video import VideoStep

    probe = kwargs.pop("probe", lambda path: {"time": 65_000, "width": 1920, "height": 1080})
    return VideoStep(MainWindowAdapter(main), probe=probe, **kwargs)


def test_video_step_accepts_media_rejects_others_and_expands_folders(tmp_path):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"0")
    notes = tmp_path / "notes.txt"
    notes.write_text("x", encoding="utf-8")
    folder = tmp_path / "batch"
    folder.mkdir()
    (folder / "one.mkv").write_bytes(b"0")
    (folder / "two.mp3").write_bytes(b"0")
    main = _main()
    step = _video_step(main, tmp_path)
    assert not step.is_ready()

    step.add_files([str(clip), str(notes), str(folder), str(clip)])

    assert [Path(p).name for p in step.files()] == ["clip.mp4", "one.mkv", "two.mp3"]
    assert step.is_ready()
    assert main.win_action.queue_mp4 == step.files()
    assert "notes.txt" in step.message.text()
    assert step.total_duration_ms() == 3 * 65_000

    step.remove_file(step.files()[0])
    assert [Path(p).name for p in step.files()] == ["one.mkv", "two.mp3"]


def test_video_step_describes_media_and_unreadable_files(tmp_path):
    from videotrans.ui.wizard.step_video import describe_media

    assert describe_media({"time": 3_725_000, "width": 1280, "height": 720}) == "1:02:05 · 1280×720"
    assert describe_media({"time": 5_000, "video_streams": 0}) == "0:05 · " + tr("wizard_audio_only")

    clip = tmp_path / "broken.mp4"
    clip.write_bytes(b"0")

    def broken(_path):
        raise RuntimeError("bad file")

    step = _video_step(_main(), tmp_path, probe=broken)
    step.add_files([str(clip)])
    assert step.is_ready()
    label = step.file_list.itemWidget(step.file_list.item(0)).findChild(QLabel)
    assert tr("wizard_unreadable") in label.text()


def test_video_step_output_folder_and_purpose(tmp_path):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"0")
    main = _main()
    step = _video_step(main, tmp_path, choose_folder=lambda: str(tmp_path / "out"))
    step.add_files([str(clip)])

    assert "_video_out" in step.output_label.text()
    step._pick_folder()
    assert main.target_dir.endswith("/out")
    assert "out" in step.output_label.text()

    assert step.purpose() == PURPOSE_SUBTITLES_ONLY
    step.set_purpose(PURPOSE_SRT_ONLY)
    assert step.purpose() == PURPOSE_SRT_ONLY
    assert main.app_mode == APP_MODE_EXTRACT


# ------------------------------------------------------------------- step 2
def _options(main):
    from videotrans.ui.wizard.step_options import OptionsStep

    return OptionsStep(MainWindowAdapter(main), total_duration=lambda: 125_000, video_count=lambda: 2)


def test_options_require_target_language_except_srt_only():
    main = _main(target_index=0)
    step = _options(main)

    assert not step.is_ready()
    assert not step.target_hint.isHidden()
    step.target_language.setCurrentIndex(1)
    assert main.target_language.currentIndex() == 1
    assert step.is_ready()

    main.target_language.setCurrentIndex(0)
    main.app_mode = APP_MODE_EXTRACT
    step.refresh()
    assert step.is_ready()
    assert step.voice_section.isHidden()


def test_options_summary_shows_free_cost_by_default_and_key_when_needed():
    main = _main()
    main.voice_role.setCurrentText("HoaiMy")
    step = _options(main)

    assert step.cost.text() == tr("wizard_cost_free")
    assert "2 · 2:05" in step.summary.text()

    main.translate_type.setCurrentIndex(translator.CHATGPT_INDEX)
    assert tr("wizard_cost_key") in step.cost.text()
    assert tr("wizard_kind_translation") in step.cost.text()


def test_subtitle_tiles_drive_existing_subtitle_type():
    main = _main()
    step = _options(main)

    step.subtitle_buttons[2].click()
    assert main.subtitle_type.currentIndex() == 2
    main.subtitle_type.setCurrentIndex(0)
    assert step.subtitle_buttons[0].isChecked()


def test_advanced_mirrors_existing_controls_and_opens_classic():
    main = _main()
    step = _options(main)

    assert set(step.advanced_combos) == {"recogn_type", "model_name", "translate_type", "tts_type"}
    assert set(step.advanced_checks) == {"voice_autorate", "video_autorate", "is_separate", "enable_cuda"}
    assert step.advanced.isHidden()
    step.advanced_toggle.setChecked(True)
    assert not step.advanced.isHidden()

    step.advanced_combos["translate_type"].setCurrentIndex(translator.MICROSOFT_INDEX)
    assert main.translate_type.currentIndex() == translator.MICROSOFT_INDEX
    step.advanced_checks["video_autorate"].setChecked(True)
    assert main.video_autorate.isChecked()
    step.all_options.click()
    assert main.shown == ["workspace"]


def test_preview_button_uses_existing_listen_action():
    main = _main()
    main.voice_role.setCurrentText("HoaiMy")
    step = _options(main)

    assert step.preview_button.isEnabled()
    step.preview_button.click()
    assert main.win_action.calls[-1] == "listen"


# --------------------------------------------------------------- wiring
def test_main_window_attaches_pages_and_validators(tmp_path):
    from videotrans.mainwin.main_win import MainWindow
    from videotrans.ui.wizard import WizardShell

    main = _main(target_index=0)
    main.wizard = WizardShell()
    main._wizard_translate_another = lambda: MainWindow._wizard_translate_another(main)
    main._wizard_step_changed = lambda step: MainWindow._wizard_step_changed(main, step)
    MainWindow._attach_wizard_pages(main)

    assert main.wizard.pages.widget(0) is main.wizard_video
    assert main.wizard.pages.widget(1) is main.wizard_options
    assert not main.wizard.next_button.isEnabled()

    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"0")
    main.wizard_video._probe = lambda path: {"time": 1000}
    main.wizard_video.add_files([str(clip)])
    assert main.wizard.next_button.isEnabled()
    main.wizard.next()
    assert not main.wizard.next_button.isEnabled()
    main.wizard_options.target_language.setCurrentIndex(1)
    assert main.wizard.next_button.isEnabled()
    main.wizard.next()
    assert main.wizard.pages.widget(2) is main.wizard_run
    assert not main.wizard_run.ready.isHidden()
    main.win_action.queue_mp4 = []  # the classic action clears its queue after a job
    main.wizard.back()
    main.wizard.next()
    assert main.win_action.queue_mp4 == main.wizard_video.files()
    main._wizard_translate_another()
    assert main.wizard_video.files() == []
    assert main.wizard.current_step() == 0
