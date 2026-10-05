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
