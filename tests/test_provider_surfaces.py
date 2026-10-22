import importlib.util
from pathlib import Path

import pytest

from videotrans import recognition, translator, tts
from videotrans.ui.provider_visibility import (
    CURATED_PROVIDER_IDS,
    RECOGNITION,
    TRANSLATION,
    TTS,
    curated_first_provider_ids,
    is_hidden_by_default,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_audit():
    spec = importlib.util.spec_from_file_location(
        "audit_provider_surfaces", ROOT / "scripts" / "audit_provider_surfaces.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_desktop_provider_combo_is_registered():
    assert _load_audit().audit(ROOT) == []


def test_audit_flags_an_unregistered_provider_combo():
    audit = _load_audit()
    source = (
        "from videotrans import tts\n"
        "def build(win):\n"
        "    win.tts_type.addItems(tts.TTS_NAME_LIST)\n"
    )
    assert audit.find_unregistered(source) == [(3, "win.tts_type")]

    registered = source + "    register_provider_combo(win.tts_type, TTS)\n"
    assert audit.find_unregistered(registered) == []


@pytest.mark.parametrize(
    ("kind", "names"),
    (
        (TRANSLATION, translator.TRANSLASTE_NAME_LIST),
        (RECOGNITION, recognition.RECOGN_NAME_LIST),
        (TTS, tts.TTS_NAME_LIST),
    ),
)
def test_curated_first_order_is_a_permutation_with_curated_prefix(kind, names):
    ordered = curated_first_provider_ids(kind)
    curated_count = len(CURATED_PROVIDER_IDS[kind])

    assert sorted(ordered) == list(range(len(names)))
    assert set(ordered[:curated_count]) == set(CURATED_PROVIDER_IDS[kind])
    assert all(is_hidden_by_default(kind, provider_id) for provider_id in ordered[curated_count:])


def test_webui_choices_keep_registry_names_as_values():
    webui = pytest.importorskip("webui")

    for kind, names, to_index in (
        (RECOGNITION, webui.RECOGN_NAMES, webui._recogn_index_from_display),
        (TRANSLATION, webui.TRANSLATE_NAMES, webui._translate_index_from_display),
        (TTS, webui.TTS_NAMES, webui._tts_index_from_display),
    ):
        choices = webui._provider_choices(kind, names)
        assert sorted(value for _, value in choices) == sorted(names)
        first_label, first_value = choices[0]
        assert first_label == first_value
        assert not is_hidden_by_default(kind, to_index(first_value))
        for label, value in choices:
            hidden = is_hidden_by_default(kind, to_index(value))
            assert label.endswith("(Advanced)") is hidden


def test_cli_lists_every_index_and_marks_advanced(capsys):
    from cli import list_providers

    list_providers()
    out = capsys.readouterr().out

    assert f" {translator.GOOGLE_INDEX:2d} = {translator.TRANSLASTE_NAME_LIST[translator.GOOGLE_INDEX]}\n" in out
    assert f" {translator.DEEPSEEK_INDEX:2d} = {translator.TRANSLASTE_NAME_LIST[translator.DEEPSEEK_INDEX]} [advanced]" in out
    assert f" {tts.AZURE_TTS:2d} = {tts.TTS_NAME_LIST[tts.AZURE_TTS]} [advanced]" in out


def test_cli_examples_use_vietnamese_voice():
    source = (ROOT / "cli.py").read_text(encoding="utf-8")

    assert "zh-CN-YunyangNeural" not in source
    assert "vi-VN-HoaiMyNeural" in source
