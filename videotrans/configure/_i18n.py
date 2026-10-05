# -*- coding: utf-8 -*-
import json
import os
from functools import lru_cache
from pathlib import Path

from videotrans.configure._paths import ROOT_DIR

# Module-level state, set via _init_language()
defaulelang = None
_transobj = None
UI_LOCALES = ('vi_VN', 'en_US')


@lru_cache(maxsize=None)
def _get_langjson_list():
    lang_dir = Path(f'{ROOT_DIR}/videotrans/language')
    _SUPPORT_LANG = {}
    if lang_dir.exists():
        for locale in UI_LOCALES:
            it = lang_dir / f'{locale}.json'
            if it.is_file() and it.stat().st_size > 0:
                _SUPPORT_LANG[locale] = it.as_posix()
    return _SUPPORT_LANG


@lru_cache()
def _get_transobj(lang:str=None):
    SUPPORT_LANG = _get_langjson_list()
    _tobj={}
    if not lang:
        return _tobj
    for n in [lang,lang.split('_')[0].lower()]:
        _langfile=SUPPORT_LANG.get(n)
        if _langfile and Path(_langfile).exists():
            try:
                _tobj = json.loads(Path(_langfile).read_text(encoding='utf-8'))
            except Exception as e:
                Path(f'{ROOT_DIR}/start_error.txt').write_text(f"{e}")
    return _tobj

def _normalize_ui_locale(value):
    """Resolve UI aliases; legacy Chinese UI settings migrate to English."""
    if not isinstance(value, str):
        return value
    aliases = {'en': 'en_US', 'en-us': 'en_US', 'zh': 'en_US',
               'zh-cn': 'en_US', 'zh-tw': 'en_US', 'vi': 'vi_VN',
               'vi-vn': 'vi_VN'}
    return aliases.get(value.strip().lower().replace('_', '-'), value)


def _init_language(settings):
    global defaulelang, _transobj
    SUPPORT_LANG = _get_langjson_list()
    original = settings.lang
    saved = _normalize_ui_locale(original) if original else 'vi_VN'
    if saved not in SUPPORT_LANG:
        saved = 'vi_VN' if 'vi_VN' in SUPPORT_LANG else 'en_US'
    requested = os.environ.get('PYVIDEOTRANS_LANG')
    selected = _normalize_ui_locale(requested) if requested else saved
    _lang = selected if selected in SUPPORT_LANG else saved
    if not original:
        saved = _lang
    if settings.lang != saved:
        settings.lang = saved
        settings.save()
    defaulelang = _lang
    _transobj = _get_transobj(defaulelang)
    return defaulelang, _transobj


def tr(lang_key, *kw):
    global _transobj
    if not _transobj:
        _transobj = _get_transobj(defaulelang)
    if not _transobj:
        return lang_key

    if isinstance(lang_key, list):
        str_list = [t for t in [_transobj.get(it) for it in lang_key] if t]
        return ",".join(str_list)
    lang = _transobj.get(lang_key)
    if not lang:
        return lang_key
    if not kw:
        return lang
    try:
        return lang.format(*kw)
    except IndexError:
        return lang
