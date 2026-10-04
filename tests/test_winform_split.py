from types import SimpleNamespace
from unittest.mock import Mock

from videotrans import winform


def test_helpers_importable():
    from videotrans.winform._helpers import make_feed_translator, make_feed_stt, make_feed_tts, make_setallmodels
    assert callable(make_feed_translator)
    assert callable(make_feed_stt)
    assert callable(make_feed_tts)
    assert callable(make_setallmodels)


def test_get_win_loads_window_on_demand_and_reuses_it(monkeypatch):
    window = SimpleNamespace(show=Mock(), activateWindow=Mock())
    module = SimpleNamespace(openwin=Mock(return_value=window))
    importer = Mock(return_value=module)
    monkeypatch.setattr(winform.app_cfg, "child_forms", {})
    monkeypatch.setattr(winform.importlib, "import_module", importer)

    assert winform.get_win("example") is window
    assert winform.get_win("example") is None
    importer.assert_called_once_with(".example", package=winform.__package__)
    module.openwin.assert_called_once_with()
    assert window.show.call_count == 2
    window.activateWindow.assert_called_once_with()


def test_get_cls_caches_imported_ui_module(monkeypatch):
    ui_class = type("Ui_example", (), {})
    importer = Mock(return_value=SimpleNamespace(Ui_example=ui_class))
    monkeypatch.setattr(winform, "_loaded_modules", {})
    monkeypatch.setattr(winform.importlib, "import_module", importer)

    assert winform.get_cls("example") is ui_class
    assert winform.get_cls("example") is ui_class
    importer.assert_called_once_with("..ui.example", package=winform.__package__)


def test_helpers_factory_returns_callable():
    from videotrans.winform._helpers import make_setallmodels
    mock_form = type('MockForm', (), {
        'edit_allmodels': type('W', (), {'toPlainText': lambda self: 'm1,m2'})()
    })()
    fn = make_setallmodels(mock_form, 'model_widget', 'settings_key')
    assert callable(fn)
