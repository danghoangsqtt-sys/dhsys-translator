"""Exercise the action mixins against Qt controls without starting media jobs."""

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QWidget

from videotrans.mainwin._actions_base_misc import WinActionBaseMiscMixin
from videotrans.mainwin._actions_base_mode import WinActionBaseModeMixin
from videotrans.mainwin._actions_check import WinActionCheckMixin


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize('voice,video,expected_hidden', [
    (True, False, True), (False, True, True), (False, False, False),
])
def test_autorate_controls_silent_gap_visibility(app, voice, video, expected_hidden):
    main = SimpleNamespace(
        video_autorate=QCheckBox(), voice_autorate=QCheckBox(),
        remove_silent_mid=QWidget(), align_sub_audio=QWidget(),
    )
    main.video_autorate.setChecked(video)
    main.voice_autorate.setChecked(voice)
    action = SimpleNamespace(main=main)
    WinActionBaseMiscMixin.check_voice_autorate(action, voice)
    WinActionBaseMiscMixin.check_video_autorate(action, video)
    assert main.remove_silent_mid.isHidden() is expected_hidden
    assert main.align_sub_audio.isHidden() is expected_hidden


@pytest.mark.parametrize('subtitle_type,expected_hidden', [(1, True), (3, False)])
def test_subtitle_type_controls_srt_output(app, subtitle_type, expected_hidden):
    output_srt = QComboBox()
    output_srt.addItems(['None', 'Source', 'Target'])
    action = SimpleNamespace(main=SimpleNamespace(output_srt=output_srt))
    WinActionCheckMixin.set_subtitle_type(action, subtitle_type)
    assert output_srt.isHidden() is expected_hidden
    if not expected_hidden:
        assert output_srt.currentIndex() == 2


@pytest.mark.parametrize('mode,expected_role', [('tiqu', 'No'), ('biaozhun', 'voice')])
def test_set_mode_updates_real_controls(app, mode, expected_role):
    subtitle_type = QComboBox()
    subtitle_type.addItems(['None', 'Hard'])
    subtitle_type.setCurrentIndex(1)
    voice_role = QComboBox()
    voice_role.addItems(['No', 'voice'])
    voice_role.setCurrentText('voice')
    main = SimpleNamespace(
        app_mode=mode, subtitle_type=subtitle_type, voice_role=voice_role,
        copysrt_rawvideo=QCheckBox(),
    )
    main.copysrt_rawvideo.setChecked(True)
    action = SimpleNamespace(main=main, cfg={'voice_role': 'voice'})
    WinActionBaseModeMixin.set_mode(action)
    assert action.cfg['voice_role'] == expected_role
    if mode == 'tiqu':
        assert action.cfg['subtitle_type'] == 0
        assert action.cfg['copysrt_rawvideo'] is True


def test_standard_mode_does_not_silently_turn_no_subtitles_into_extract_mode(app):
    subtitle_type = QComboBox()
    subtitle_type.addItems(['No subtitles', 'Always visible'])
    subtitle_type.setCurrentIndex(0)
    voice_role = QComboBox()
    voice_role.addItems(['No', 'voice'])
    main = SimpleNamespace(
        app_mode='biaozhun', subtitle_type=subtitle_type, voice_role=voice_role,
        copysrt_rawvideo=QCheckBox(),
    )
    action = SimpleNamespace(main=main, cfg={'subtitle_type': 0, 'voice_role': 'No'})

    WinActionBaseModeMixin.set_mode(action)

    assert main.app_mode == 'biaozhun'
    assert action.cfg['subtitle_type'] == 0


def test_no_subtitle_video_requires_explicit_confirmation(app, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    subtitle_type = QComboBox()
    subtitle_type.addItems(['No subtitles', 'Always visible'])
    subtitle_type.setCurrentIndex(0)
    action = SimpleNamespace(main=SimpleNamespace(
        app_mode='biaozhun', subtitle_type=subtitle_type,
    ))
    answers = iter([
        QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    ])
    monkeypatch.setattr(QMessageBox, 'warning', lambda *args, **kwargs: next(answers))

    assert WinActionCheckMixin.confirm_no_subtitle_output(action) is False
    assert WinActionCheckMixin.confirm_no_subtitle_output(action) is True

    action.main.app_mode = 'tiqu'
    assert WinActionCheckMixin.confirm_no_subtitle_output(action) is True
