"""The desktop language flag must take effect before configuration import."""

import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize('flag,locale', [
    ('en', 'en_US'), ('zh', 'en_US'), ('zh-cn', 'en_US'),
    ('zh_CN', 'en_US'), ('zh-tw', 'en_US'),
    ('vi', 'vi_VN'), ('vi-vn', 'vi_VN'),
])
def test_desktop_language_flag_precedes_config_import(flag, locale):
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'
    env['PYVIDEOTRANS_LANG'] = 'vi_VN' if flag.startswith('zh') else 'zh_CN'
    script = (
        "import sys; sys.argv=['sp.py', '--lang', sys.argv[1]]; "
        "import sp; from videotrans.configure import config; "
        "print('SELECTED_LOCALE=' + config.defaulelang)"
    )
    result = subprocess.run([sys.executable, '-c', script, flag],
                            capture_output=True, text=True, env=env, timeout=30, check=True)
    assert f'SELECTED_LOCALE={locale}' in result.stdout


def test_legacy_chinese_ui_setting_migrates_without_losing_other_settings(monkeypatch):
    from videotrans.configure import _i18n

    class Settings:
        lang = 'zh_CN'
        proxy = 'http://127.0.0.1:7890'
        saved = 0

        def save(self):
            self.saved += 1

    monkeypatch.delenv('PYVIDEOTRANS_LANG', raising=False)
    settings = Settings()
    locale, _ = _i18n._init_language(settings)
    assert locale == settings.lang == 'en_US'
    assert settings.proxy == 'http://127.0.0.1:7890'
    assert settings.saved == 1


def test_legacy_chinese_catalog_cannot_become_ui_locale(tmp_path, monkeypatch):
    from videotrans.configure import _i18n

    lang_dir = tmp_path / 'videotrans' / 'language'
    lang_dir.mkdir(parents=True)
    for name in ('vi_VN', 'en_US', 'zh_CN'):
        (lang_dir / f'{name}.json').write_text('{}', encoding='utf-8')
    monkeypatch.setattr(_i18n, 'ROOT_DIR', str(tmp_path))
    _i18n._get_langjson_list.cache_clear()
    try:
        assert set(_i18n._get_langjson_list()) == {'vi_VN', 'en_US'}
    finally:
        _i18n._get_langjson_list.cache_clear()


@pytest.mark.parametrize('flag,heading', [
    ('vi', 'Cài đặt chung'), ('en', 'General'),
])
def test_settings_page_labels_and_tooltips_follow_supported_locale(flag, heading):
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYVIDEOTRANS_LANG'] = flag
    script = (
        "import re; from videotrans.ui.setini import notices, titles, heads; "
        "values=[*titles.values(), *heads.values(), "
        "*(text for group in notices.values() for text in group.values())]; "
        "assert len(values) >= 200; "
        "assert not any(re.search('[\\u4e00-\\u9fff]', text) for text in values); "
        "print('SETTINGS_HEADING=' + heads['common'])"
    )
    result = subprocess.run([sys.executable, '-c', script],
                            capture_output=True, text=True, encoding='utf-8',
                            env=env, timeout=30, check=True)
    assert f'SETTINGS_HEADING={heading}' in result.stdout


def test_legal_terms_are_readable_in_both_ui_locales():
    import re

    from PySide6.QtGui import QTextDocument
    from videotrans.ui._legal_terms import legal_terms_html

    for locale, heading in (
        ('en_US', 'Software License and Service Agreement'),
        ('vi_VN', 'Giấy phép và điều khoản dịch vụ'),
    ):
        html = legal_terms_html(locale)
        document = QTextDocument()
        document.setHtml(html)
        text = document.toPlainText()
        assert heading in text
        assert 'GPLv3' in text
        assert 'https://github.com/jianchang512/pyvideotrans' in html
        assert len(text) > 3000
        assert not re.search(r'[\u4e00-\u9fff]', text)
