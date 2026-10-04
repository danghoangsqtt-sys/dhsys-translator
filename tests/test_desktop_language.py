"""The desktop language flag must take effect before configuration import."""

import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize('flag,locale', [('en', 'en_US'), ('zh', 'zh_CN'), ('zh-cn', 'zh_CN')])
def test_desktop_language_flag_precedes_config_import(flag, locale):
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'
    env['PYVIDEOTRANS_LANG'] = 'en_US' if locale == 'zh_CN' else 'zh_CN'
    script = (
        "import sys; sys.argv=['sp.py', '--lang', sys.argv[1]]; "
        "import sp; from videotrans.configure import config; "
        "print('SELECTED_LOCALE=' + config.defaulelang)"
    )
    result = subprocess.run([sys.executable, '-c', script, flag],
                            capture_output=True, text=True, env=env, timeout=30, check=True)
    assert f'SELECTED_LOCALE={locale}' in result.stdout
