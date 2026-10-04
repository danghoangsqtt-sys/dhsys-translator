from unittest.mock import Mock

from videotrans.mainwin._lifecycle import LifecycleMixin


def test_gui_close_terminates_only_ffmpeg_descendants(monkeypatch):
    owned = Mock()
    owned.name.return_value = "ffmpeg.exe"
    ordinary_child = Mock()
    ordinary_child.name.return_value = "python.exe"
    unrelated_ffmpeg = Mock()
    unrelated_ffmpeg.name.return_value = "ffmpeg.exe"
    parent = Mock()
    parent.children.return_value = [owned, ordinary_child]
    monkeypatch.setattr("videotrans.mainwin._lifecycle.psutil.Process", lambda: parent)
    wait_procs = Mock(return_value=([owned], []))
    monkeypatch.setattr("videotrans.mainwin._lifecycle.psutil.wait_procs", wait_procs)

    LifecycleMixin.kill_ffmpeg_processes()

    parent.children.assert_called_once_with(recursive=True)
    owned.terminate.assert_called_once_with()
    ordinary_child.terminate.assert_not_called()
    unrelated_ffmpeg.terminate.assert_not_called()
    wait_procs.assert_called_once_with([owned], timeout=3)


def test_stubborn_owned_ffmpeg_is_killed_after_timeout(monkeypatch):
    owned = Mock()
    owned.name.return_value = "ffmpeg"
    parent = Mock()
    parent.children.return_value = [owned]
    monkeypatch.setattr("videotrans.mainwin._lifecycle.psutil.Process", lambda: parent)
    monkeypatch.setattr("videotrans.mainwin._lifecycle.psutil.wait_procs",
                        Mock(return_value=([], [owned])))

    LifecycleMixin.kill_ffmpeg_processes()

    owned.terminate.assert_called_once_with()
    owned.kill.assert_called_once_with()
