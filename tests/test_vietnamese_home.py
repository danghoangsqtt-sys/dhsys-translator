import json
import re
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from videotrans.ui.home import HomePage


app = QApplication.instance() or QApplication([])


def test_home_routes_to_existing_tools_and_workspace():
    page = HomePage('vi_VN')
    routes = []
    workspaces = []
    page.tool_requested.connect(routes.append)
    page.workspace_requested.connect(lambda: workspaces.append(True))

    page.findChild(QPushButton, 'openWorkspace').click()
    for name in ('fn_recogn', 'fn_fanyisrt', 'fn_peiyinrole', 'fn_vas'):
        page.findChild(QPushButton, f'open_{name}').click()

    assert workspaces == [True]
    assert routes == ['fn_recogn', 'fn_fanyisrt', 'fn_peiyinrole', 'fn_vas']


def test_home_language_choice_emits_locale():
    page = HomePage('vi_VN')
    assert [page.language.itemData(i) for i in range(page.language.count())] == ['vi_VN', 'en_US']
    selected = []
    page.locale_requested.connect(selected.append)
    page.language.setCurrentIndex(page.language.findData('en_US'))
    assert selected == ['en_US']
    page.reset_locale('vi_VN')
    assert page.language.currentData() == 'vi_VN'
    assert selected == ['en_US']


def test_splash_uses_vietnamese_copy_without_legacy_site(monkeypatch):
    monkeypatch.setenv('PYVIDEOTRANS_LANG', 'vi')
    from sp import StartWindow

    splash = StartWindow()
    labels = ' '.join(label.text() for label in splash.findChildren(QLabel))
    assert 'XƯỞNG VIDEO' in labels
    assert 'Đang chuẩn bị' in labels
    assert 'pyvideotrans.com' not in labels.lower()


def test_vietnamese_catalog_covers_english_keys_and_format_fields():
    language_dir = Path(__file__).resolve().parents[1] / 'videotrans' / 'language'
    english = json.loads((language_dir / 'en_US.json').read_text(encoding='utf-8'))
    vietnamese = json.loads((language_dir / 'vi_VN.json').read_text(encoding='utf-8'))
    fields = re.compile(r'\{[^{}]*\}')

    assert english.keys() <= vietnamese.keys()
    for key, english_text in english.items():
        assert sorted(fields.findall(english_text)) == sorted(fields.findall(vietnamese[key])), key
