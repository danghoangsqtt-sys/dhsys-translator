from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QLabel

from videotrans import tts
from videotrans.component.onlyone_set_role import SpeakerAssignmentDialog
from videotrans.configure.config import app_cfg
from videotrans.mainwin._actions_config import WinActionConfigMixin
from videotrans.task import _stage_dubbing
from videotrans.util import help_role


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_local_vieneu_roles_are_merged_without_overwriting_saved_roles(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": [
                    {"id": "Adam", "gender": "male"},
                    {"id": "Thục Đoan", "gender": "female"},
                    {"id": "Saved Voice", "gender": "male"},
                ]
            }

    monkeypatch.setitem(help_role.params, "openaitts_api", "http://127.0.0.1:8000/v1")
    monkeypatch.setitem(help_role.params, "openaitts_model", "vieneu-v3-turbo")
    monkeypatch.setitem(help_role.params, "openaitts_role", "Saved Voice,Manual Voice")

    import requests

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: Response())

    roles = help_role.role_menu(tts.OPENAI_TTS, "vi")

    assert roles == ["No", "Saved Voice", "Manual Voice", "Adam", "Thục Đoan"]
    assert help_role.params["openaitts_role"] == "Saved Voice,Manual Voice"


def test_local_vieneu_discovery_failure_keeps_saved_roles(monkeypatch):
    monkeypatch.setitem(help_role.params, "openaitts_api", "http://localhost:8000/v1")
    monkeypatch.setitem(help_role.params, "openaitts_model", "vieneu-v3-turbo")
    monkeypatch.setitem(help_role.params, "openaitts_role", "Adam,Thái Sơn")

    import requests

    def fail(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests, "get", fail)

    assert help_role.role_menu(tts.OPENAI_TTS, "vi") == ["No", "Adam", "Thái Sơn"]


def test_local_vieneu_with_no_saved_roles_shows_discovered_voices_only(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"data": [{"id": "Adam"}, {"id": "Thục Đoan"}]}

    monkeypatch.setitem(help_role.params, "openaitts_api", "http://127.0.0.1:8000/v1")
    monkeypatch.setitem(help_role.params, "openaitts_model", "vieneu-v3-turbo")
    monkeypatch.setitem(help_role.params, "openaitts_role", "")

    import requests

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: Response())

    assert help_role.role_menu(tts.OPENAI_TTS, "vi") == ["No", "Adam", "Thục Đoan"]


def test_remote_openai_compatible_url_does_not_trigger_voice_discovery(monkeypatch):
    monkeypatch.setitem(help_role.params, "openaitts_api", "https://example.com/v1")
    monkeypatch.setitem(help_role.params, "openaitts_model", "vieneu-v3-turbo")
    monkeypatch.setitem(help_role.params, "openaitts_role", "alloy,verse")

    import requests

    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: pytest.fail("remote voice discovery must not run"),
    )

    assert help_role.role_menu(tts.OPENAI_TTS, "vi") == ["No", "alloy", "verse"]


def test_main_voice_dropdown_keeps_selected_discovered_vieneu_voice(app, monkeypatch):
    target_language = QComboBox()
    target_language.addItem("Vietnamese")
    voice_role = QComboBox()
    voice_role.addItems(["No", "Adam", "Thái Sơn"])
    voice_role.setCurrentText("Thái Sơn")
    show_tips = QLabel()
    main = SimpleNamespace(
        target_language=target_language,
        voice_role=voice_role,
        show_tips=show_tips,
        current_rolelist=[],
    )
    action = SimpleNamespace(main=main)

    from videotrans.mainwin import _actions_config

    monkeypatch.setattr(_actions_config.translator, "get_code", lambda **kwargs: "vi")
    monkeypatch.setattr(_actions_config.tts, "is_allow_lang", lambda **kwargs: True)
    monkeypatch.setattr(_actions_config.tts, "is_input_api", lambda **kwargs: True)
    monkeypatch.setattr(
        _actions_config,
        "role_menu",
        lambda *args, **kwargs: ["No", "Adam", "Thái Sơn", "Thục Đoan"],
    )

    WinActionConfigMixin.tts_type_change(action, tts.OPENAI_TTS)

    assert main.current_rolelist == ["No", "Adam", "Thái Sơn", "Thục Đoan"]
    assert main.voice_role.currentText() == "Thái Sơn"


def test_speaker_assignment_can_keep_distinct_male_and_female_roles(app):
    male = QCheckBox()
    female = QCheckBox()
    male.setChecked(True)
    female.setChecked(False)
    male_label = QLabel()
    female_label = QLabel()
    combo = QComboBox()
    combo.addItems(["No", "Adam", "Thục Đoan"])

    dialog = SimpleNamespace(
        speaker_combo=combo,
        speaker_checks={male: "spk0", female: "spk1"},
        speaker_labels={male: male_label, female: female_label},
        speakers={"spk0": None, "spk1": None},
        _update_role_column=lambda: None,
    )

    combo.setCurrentText("Adam")
    SpeakerAssignmentDialog.assign_speaker_roles(dialog)
    female.setChecked(True)
    combo.setCurrentText("Thục Đoan")
    SpeakerAssignmentDialog.assign_speaker_roles(dialog)

    assert dialog.speakers == {"spk0": "Adam", "spk1": "Thục Đoan"}


def test_dubbing_queue_uses_per_line_voice_without_changing_subtitle_text(monkeypatch):
    target_subs = [
        {
            "line": 1,
            "text": "Xin chào Adam.",
            "start_time": 0,
            "end_time": 1000,
            "startraw": "00:00:00,000",
            "endraw": "00:00:01,000",
        },
        {
            "line": 2,
            "text": "Xin chào Thục Đoan.",
            "start_time": 1000,
            "end_time": 2000,
            "startraw": "00:00:01,000",
            "endraw": "00:00:02,000",
        },
    ]
    source_subs = [dict(item) for item in target_subs]
    calls = []

    monkeypatch.setattr(
        _stage_dubbing,
        "get_subtitle_from_srt",
        lambda path: target_subs if path == "target.srt" else source_subs,
    )
    monkeypatch.setattr(_stage_dubbing, "vail_file", lambda path: False)
    monkeypatch.setattr(_stage_dubbing, "prepare_tts_text", lambda text, **kwargs: text)
    monkeypatch.setattr(
        _stage_dubbing,
        "run_tts",
        lambda **kwargs: calls.extend(kwargs["queue_tts"]),
    )
    monkeypatch.setitem(_stage_dubbing.settings, "save_segment_audio", False)
    monkeypatch.setattr(app_cfg, "line_roles", {"1": "Adam", "2": "Thục Đoan"})

    worker = SimpleNamespace(
        should_dubbing=True,
        cfg=SimpleNamespace(
            target_sub="target.srt",
            source_sub="source.srt",
            voice_rate="+0%",
            voice_role="Thái Sơn",
            volume="+0%",
            pitch="+0Hz",
            tts_type=tts.OPENAI_TTS,
            target_language_code="vi",
            target_dir="output",
            cache_folder="cache",
            detect_language="vi",
            is_cuda=False,
            noextname="demo",
            fix_punc=0,
        ),
        uuid="voice-selection-test",
        queue_tts=[],
        _create_ref_from_vocal=lambda: None,
        _save_srt_target=lambda queue, path: None,
    )

    _stage_dubbing.DubbingMixin._tts(worker)

    assert [item["role"] for item in calls] == ["Adam", "Thục Đoan"]
    assert [item["text"] for item in calls] == ["Xin chào Adam.", "Xin chào Thục Đoan."]
