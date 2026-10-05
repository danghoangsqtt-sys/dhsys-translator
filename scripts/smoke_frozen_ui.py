"""Verify the packaged Vietnamese start page and its navigation signals."""

import json
import os
from pathlib import Path
import sys
import tempfile
import traceback
from types import SimpleNamespace


def run_check():
    if not getattr(sys, 'frozen', False):
        raise AssertionError('run this probe through the packaged sp.exe')
    requested_locale = sys.argv[2] if len(sys.argv) > 2 else 'vi'
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    os.environ['PYVIDEOTRANS_LANG'] = requested_locale

    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QCheckBox,
        QComboBox,
        QFrame,
        QMainWindow,
        QMessageBox,
        QPushButton,
    )
    from videotrans.configure.config import ROOT_DIR, app_cfg, defaulelang, params, settings, tr
    from videotrans.configure._paths import resource_path
    from videotrans.ui.home import HomePage
    from videotrans.ui.info import Ui_info
    from videotrans.ui.en import Ui_MainWindow
    from videotrans.ui.workspace_shell import WorkspaceShell

    app = QApplication.instance() or QApplication([])
    normalized_locale = requested_locale.lower().replace('_', '-')
    expected_locale = 'en_US' if normalized_locale in {'en', 'en-us', 'zh', 'zh-cn', 'zh-tw'} else 'vi_VN'
    expected_brand = 'Video Workshop' if expected_locale == 'en_US' else 'Xưởng Video'
    if defaulelang != expected_locale or tr('Video Workshop') != expected_brand:
        raise AssertionError(f'locale resolution failed: requested={requested_locale}, selected={defaulelang}')
    if not resource_path('videotrans', 'language', 'vi_VN.json').is_file():
        raise AssertionError('Vietnamese catalog missing from package')
    if not resource_path('videotrans', 'language', 'en_US.json').is_file():
        raise AssertionError('English catalog missing from package')
    if resource_path('videotrans', 'language', 'zh_CN.json').exists():
        raise AssertionError('Chinese UI catalog must not be bundled')
    legacy_request = normalized_locale in {'zh', 'zh-cn', 'zh-tw'}
    legacy_catalog = Path(ROOT_DIR) / 'videotrans' / 'language' / 'zh_CN.json'
    if legacy_request and (not legacy_catalog.is_file() or settings.lang != 'en_US'):
        raise AssertionError('legacy Chinese user data was not ignored and migrated to English')

    page = HomePage(defaulelang)
    locale_choices = [page.language.itemData(index) for index in range(page.language.count())]
    if locale_choices != ['vi_VN', 'en_US']:
        raise AssertionError(f'unexpected interface locale choices: {locale_choices}')
    for width in (480, 720, 900, 1280):
        page.resize(width, 720)
        page.show()
        app.processEvents()
        cards = page.findChildren(QFrame, 'toolCard')
        if len(cards) != 4 or any(card.mapTo(page, QPoint()).x() + card.width() > page.width() for card in cards):
            raise AssertionError(f'home cards exceed the {width}px canvas')
    app.processEvents()
    routes = []
    workspaces = []
    page.tool_requested.connect(routes.append)
    page.workspace_requested.connect(lambda: workspaces.append(True))
    page.findChild(QPushButton, 'openWorkspace').click()
    for name in ('fn_recogn', 'fn_fanyisrt', 'fn_peiyinrole', 'fn_vas'):
        page.findChild(QPushButton, f'open_{name}').click()
    if routes != ['fn_recogn', 'fn_fanyisrt', 'fn_peiyinrole', 'fn_vas'] or workspaces != [True]:
        raise AssertionError(f'home navigation failed: {routes}, {workspaces}')
    about = Ui_info()
    if 'pyvideotrans.com' in about.windowTitle().lower():
        raise AssertionError('legacy website appears in About title')
    about.close()
    page.close()

    from videotrans.ui.fn_fanyisrt import Ui_fn_fanyisrt
    from videotrans.ui.fn_peiyinrole import Ui_fn_peiyinrole
    from videotrans.ui.fn_recogn import Ui_fn_recogn
    from videotrans.ui.fn_vas import Ui_fn_vas
    quick_tools = (
        (Ui_fn_fanyisrt(), ('fanyi_import', 'fanyi_start')),
        (Ui_fn_peiyinrole(), ('hecheng_importbtn', 'hecheng_startbtn')),
        (Ui_fn_vas(), ('ysphb_selectvideo', 'ysphb_startbtn')),
        (Ui_fn_recogn(), ('shibie_startbtn', 'shibie_opendir')),
    )
    for tool, controls in quick_tools:
        tool.resize(480, 720)
        tool.show()
        app.processEvents()
        if tool.width() != 480:
            raise AssertionError(f'{type(tool).__name__} did not fit 480px')
        for name in controls:
            control = getattr(tool, name)
            if control.mapTo(tool, QPoint()).x() + control.width() > tool.width():
                raise AssertionError(f'{type(tool).__name__}.{name} exceeds its window')
        tool.close()
    expected_menu = 'Menu' if expected_locale == 'en_US' else 'Danh mục'
    if tr('Menu') != expected_menu:
        raise AssertionError(f'compact-menu label is incorrect for {expected_locale}')

    class GeneratedWindow(QMainWindow, Ui_MainWindow):
        def show_home(self):
            pass

    window = GeneratedWindow()
    window.setupUi(window)
    workspace = window.takeCentralWidget()
    shell = WorkspaceShell(window, workspace)
    catalog_actions = {
        action for section in shell._catalog_sections for action in section.actions()
    }
    workflow_sections = (
        window.prepareSection,
        window.transcriptionSection,
        window.translationSection,
        window.voiceSection,
        window.outputSection,
    )
    if shell.findChild(type(workspace), 'centralwidget') is not workspace or window.fn_fanyisrt not in catalog_actions:
        raise AssertionError('packaged workspace shell did not retain original actions')
    if any(section.property('workflowSection') is not True for section in workflow_sections):
        raise AssertionError('packaged workspace is missing a workflow section')
    if (window.btn_get_video.parentWidget() is not window.prepareSection
            or window.recogn_type.parentWidget() is not window.transcriptionSection
            or window.translate_type.parentWidget() is not window.translationSection
            or window.tts_type.parentWidget() is not window.voiceSection
            or window.subtitle_type.parentWidget() is not window.outputSection):
        raise AssertionError('packaged workflow controls are not in their intended sections')
    if (window.startbtn.parentWidget() is not window.workflowActionArea
            or window.retrybtn.parentWidget() is not window.workflowActionArea
            or window.scroll_area.parentWidget() is not window.workflowActivityArea
            or window.subtitle_area.parentWidget() is not window.verticalLayoutWidget):
        raise AssertionError('packaged workspace hierarchy did not retain existing controls')
    shell.resize(900, 720)
    shell.show()
    app.processEvents()
    transcription_row = window.transcriptionSection.layout().itemAt(1).layout()
    if (not shell.sidebar.isHidden() or not shell.compact_navigation.isVisible()
            or window.workflowScroll.widget() is not window.layoutWidget
            or transcription_row.heightForWidth(440) <= transcription_row.heightForWidth(900)):
        raise AssertionError('packaged workspace does not adapt to a narrow desktop width')
    window.set_workflow_view_state('running')
    if (window.workflowStatus.property('workflowState') != 'running'
            or any(section.property('workflowState') != 'running' for section in workflow_sections)):
        raise AssertionError('packaged workflow view state did not reach every section')

    # Task 4.13: both subtitle-review dialogs stay editable and have no
    # countdown-driven auto-close behavior. Keep this probe offline by
    # suppressing the delayed media-preview callback.
    from videotrans.component import onlyone_set_recogn, onlyone_set_recogn2

    class _DialogParent:
        screen_size = (1200, 800)
        height = 800

    class _TimerStub:
        @staticmethod
        def singleShot(delay, callback):
            if delay == 0:
                callback()

    editor_checks = []
    with tempfile.TemporaryDirectory(prefix='pyvideotrans-frozen-ui-') as temporary:
        temporary = Path(temporary)
        for module, dialog_class, app_cfg_attr in (
            (onlyone_set_recogn, onlyone_set_recogn.EditRecognResultDialog, 'onlyone_source_sub'),
            (onlyone_set_recogn2, onlyone_set_recogn2.EditRecognResultDialog2, 'onlyone_target_sub'),
        ):
            subtitle_path = temporary / f'{app_cfg_attr}.srt'
            subtitle_path.write_text(
                '1\n00:00:00,000 --> 00:00:01,500\nFrozen subtitle editor\n',
                encoding='utf-8',
            )
            old_timer = module.QTimer
            old_play = dialog_class._play_segment
            old_path = getattr(app_cfg, app_cfg_attr)
            dialog = None
            try:
                module.QTimer = _TimerStub
                dialog_class._play_segment = lambda *_args: None
                setattr(app_cfg, app_cfg_attr, str(subtitle_path))
                dialog = dialog_class(parent=_DialogParent())
                dialog.load_table()
                triggers = dialog.table.editTriggers()
                expected_triggers = (
                    QAbstractItemView.DoubleClicked
                    | QAbstractItemView.SelectedClicked
                    | QAbstractItemView.EditKeyPressed
                    | QAbstractItemView.AnyKeyPressed
                )
                if dialog.table.focusPolicy() != Qt.StrongFocus:
                    raise AssertionError(f'{dialog_class.__name__} is not keyboard focusable')
                if dialog.table.selectionMode() != QAbstractItemView.SingleSelection:
                    raise AssertionError(f'{dialog_class.__name__} selection mode regressed')
                if (triggers & expected_triggers) != expected_triggers:
                    raise AssertionError(f'{dialog_class.__name__} edit triggers regressed')
                if not dialog.table.item(0, 5).flags() & Qt.ItemIsEditable:
                    raise AssertionError(f'{dialog_class.__name__} subtitle text is not editable')
                if dialog.timer is not None or dialog.stop_button is not None:
                    raise AssertionError(f'{dialog_class.__name__} restored countdown state')
                editor_checks.append(dialog_class.__name__)
            finally:
                if dialog is not None:
                    dialog.close()
                    dialog.deleteLater()
                setattr(app_cfg, app_cfg_attr, old_path)
                dialog_class._play_segment = old_play
                module.QTimer = old_timer
        app.processEvents()

        # Task 4.14: persisted subtitle enum mapping is frozen, invalid/fresh
        # values resolve to hard subtitles, bilingual ordering is preserved,
        # and a soft-output receipt tells the user to enable the track.
        from videotrans.task._stage_subtitle import SubtitleMixin
        from videotrans.task.subtitle_output import (
            SUBTITLE_TYPE_KEYS,
            build_output_receipt,
            subtitle_type_key,
        )

        expected_subtitle_keys = (
            'nosubtitle',
            'embedsubtitle',
            'softsubtitle',
            'embedsubtitle2',
            'softsubtitle2',
        )
        if SUBTITLE_TYPE_KEYS != expected_subtitle_keys:
            raise AssertionError(f'persisted subtitle mapping changed: {SUBTITLE_TYPE_KEYS}')
        if subtitle_type_key(None) != 'embedsubtitle' or subtitle_type_key(-1) != 'embedsubtitle':
            raise AssertionError('fresh/invalid subtitle selection no longer defaults to hard subtitles')

        labels_by_locale = {
            'en_US': [
                'No subtitles in the video',
                'Always visible on the video',
                'Turn on/off in the video player',
                'Always visible bilingual subtitles',
                'Bilingual subtitles: turn on/off in the player',
            ],
            'vi_VN': [
                'Video không có phụ đề',
                'Luôn hiện chữ trên video',
                'Bật/tắt phụ đề trong trình phát',
                'Luôn hiện phụ đề song ngữ',
                'Phụ đề song ngữ: bật/tắt trong trình phát',
            ],
        }
        for locale_name, expected_labels in labels_by_locale.items():
            catalog = json.loads(
                resource_path('videotrans', 'language', f'{locale_name}.json').read_text(encoding='utf-8')
            )
            if [catalog[key] for key in SUBTITLE_TYPE_KEYS] != expected_labels:
                raise AssertionError(f'subtitle labels regressed for {locale_name}')

        source = temporary / 'source.srt'
        target = temporary / 'target.srt'
        source.write_text('1\n00:00:00,000 --> 00:00:01,000\nOriginal line\n', encoding='utf-8')
        target.write_text('1\n00:00:00,000 --> 00:00:01,000\nTranslated line\n', encoding='utf-8')
        bilingual_orders = []
        for output_srt, expected_lines in (
            (1, ['Original line', 'Translated line']),
            (2, ['Translated line', 'Original line']),
        ):
            cache_dir = temporary / f'cache-{output_srt}'
            output_dir = temporary / f'output-{output_srt}'
            cache_dir.mkdir()
            output_dir.mkdir()
            processor = SimpleNamespace(cfg=SimpleNamespace(
                subtitle_type=4,
                output_srt=output_srt,
                source_sub=str(source),
                target_sub=str(target),
                source_language_code='en',
                target_language_code='vi',
                target_language='Vietnamese',
                cache_folder=str(cache_dir),
                target_dir=str(output_dir),
            ))
            processor._get_join_flag = SubtitleMixin._get_join_flag.__get__(processor)
            SubtitleMixin._process_subtitles(processor)
            visible_lines = [
                line for line in (output_dir / 'shuang.srt').read_text(encoding='utf-8').splitlines()
                if line in {'Original line', 'Translated line'}
            ]
            if visible_lines != expected_lines:
                raise AssertionError(f'bilingual subtitle order regressed: {visible_lines}')
            bilingual_orders.append(visible_lines)

        translated_video = temporary / 'translated.mp4'
        translated_video.write_bytes(b'fixture')
        receipt = build_output_receipt(SimpleNamespace(
            subtitle_type=2,
            output_srt=0,
            targetdir_mp4=str(translated_video),
            source_sub=str(source),
            target_sub=str(target),
            target_dir=str(temporary),
        ))
        if not receipt['soft_track_requires_player'] or receipt['video_path'] != str(translated_video):
            raise AssertionError(f'soft subtitle output receipt regressed: {receipt}')

        # No-subtitle remains an explicit standard-mode choice: mode updates
        # must not silently switch away, and the final action requires a
        # warning confirmation.
        from videotrans.mainwin._actions_base_mode import WinActionBaseModeMixin
        from videotrans.mainwin._actions_check import WinActionCheckMixin

        subtitle_combo = QComboBox()
        subtitle_combo.addItems(['No subtitles', 'Always visible'])
        subtitle_combo.setCurrentIndex(0)
        voice_combo = QComboBox()
        voice_combo.addItems(['No', 'voice'])
        main_stub = SimpleNamespace(
            app_mode='biaozhun',
            subtitle_type=subtitle_combo,
            voice_role=voice_combo,
            copysrt_rawvideo=QCheckBox(),
        )
        action_stub = SimpleNamespace(main=main_stub, cfg={'subtitle_type': 0, 'voice_role': 'No'})
        WinActionBaseModeMixin.set_mode(action_stub)
        if action_stub.cfg['subtitle_type'] != 0:
            raise AssertionError('standard mode silently changed explicit no-subtitle selection')
        old_warning = QMessageBox.warning
        try:
            QMessageBox.warning = lambda *_args, **_kwargs: QMessageBox.StandardButton.No
            if WinActionCheckMixin.confirm_no_subtitle_output(action_stub):
                raise AssertionError('no-subtitle output bypassed confirmation')
            QMessageBox.warning = lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes
            if not WinActionCheckMixin.confirm_no_subtitle_output(action_stub):
                raise AssertionError('confirmed no-subtitle output was rejected')
        finally:
            QMessageBox.warning = old_warning

        # Tasks 4.15/4.17: provider profiles layer on top of the frozen numeric
        # registries and Local is local-only strictly for loopback endpoints.
        from videotrans import recognition, translator, tts
        from videotrans.configure._languages_dict import EDGE_LANGUANGES_CODE
        from videotrans.ui.provider_profiles import (
            PROFILE_CUSTOM,
            PROFILE_GEMINI,
            PROFILE_LOCAL,
            ProviderSelection,
            profile_policy,
            resolve_profile_transition,
        )

        if tuple(translator.ID_NAME_DICT) != tuple(range(29)):
            raise AssertionError('translation provider IDs changed')
        if tuple(recognition.ID_NAME_DICT) != tuple(range(33)):
            raise AssertionError('recognition provider IDs changed')
        if tuple(tts.ID_NAME_DICT) != tuple(range(38)):
            raise AssertionError('TTS provider IDs changed')
        if not {'zh-cn', 'zh-tw', 'yue'} <= set(EDGE_LANGUANGES_CODE):
            raise AssertionError('Chinese media-language support regressed')
        custom_selection = ProviderSelection(8, 10, 29)
        local_transition = resolve_profile_transition(PROFILE_LOCAL, custom_selection, PROFILE_CUSTOM, None)
        gemini_transition = resolve_profile_transition(
            PROFILE_GEMINI,
            local_transition.selection,
            PROFILE_LOCAL,
            local_transition.custom_backup,
        )
        restored_transition = resolve_profile_transition(
            PROFILE_CUSTOM,
            gemini_transition.selection,
            PROFILE_GEMINI,
            gemini_transition.custom_backup,
        )
        if restored_transition.selection != custom_selection:
            raise AssertionError('custom provider selection was not restored')
        if not profile_policy(PROFILE_LOCAL, 'http://127.0.0.1:8000/v1').local_only_ready:
            raise AssertionError('loopback Local profile is not marked ready')
        if profile_policy(PROFILE_LOCAL, 'https://api.example.com/v1').local_only_ready:
            raise AssertionError('public Local endpoint was incorrectly marked local-only')

        # Task 4.16: the pronunciation layer is transient, Vietnamese-only,
        # and local VieNeu voice discovery never activates for a public URL.
        from videotrans.tts.pronunciation import prepare_tts_text
        from videotrans.util import help_role

        displayed_text = 'ChatGPT dùng API và AI.'
        spoken_text = prepare_tts_text(displayed_text, language='vi')
        if displayed_text != 'ChatGPT dùng API và AI.' or spoken_text == displayed_text:
            raise AssertionError('Vietnamese pronunciation layer did not stay transient')
        if prepare_tts_text(displayed_text, language='en') != displayed_text:
            raise AssertionError('pronunciation layer leaked into non-Vietnamese text')
        saved_openaitts = {
            key: params.get(key)
            for key in ('openaitts_role', 'openaitts_api', 'openaitts_model')
        }
        try:
            params['openaitts_role'] = 'Hải Đăng,Thục Đoan'
            params['openaitts_api'] = 'https://api.example.com/v1'
            params['openaitts_model'] = 'vieneu-pilot'
            if help_role.get_openaitts_roles() != ['No', 'Hải Đăng', 'Thục Đoan']:
                raise AssertionError('saved OpenAI-compatible voices were not preserved')
        finally:
            params.update(saved_openaitts)

    window.close()
    return {
        'requested_locale': requested_locale,
        'locale': defaulelang,
        'locale_choices': locale_choices,
        'legacy_catalog_ignored': bool(legacy_request and legacy_catalog.is_file()),
        'brand': tr('Video Workshop'),
        'routes': routes,
        'workspace_shell': True,
        'light_style': resource_path('videotrans', 'styles', 'light.qss').is_file(),
        'workflow_sections': len(workflow_sections),
        'workflow_state': 'running',
        'workflow_hierarchy': True,
        'responsive_layout': True,
        'responsive_quick_tools': True,
        'subtitle_editors': editor_checks,
        'subtitle_mapping': list(expected_subtitle_keys),
        'bilingual_orders': bilingual_orders,
        'soft_receipt_requires_player': receipt['soft_track_requires_player'],
        'no_subtitle_confirmation': True,
        'provider_registry_sizes': {
            'translation': len(translator.ID_NAME_DICT),
            'recognition': len(recognition.ID_NAME_DICT),
            'tts': len(tts.ID_NAME_DICT),
        },
        'provider_custom_restore': True,
        'local_profile_loopback_only': True,
        'pronunciation_layer_transient': True,
        'vieneu_public_discovery_blocked': True,
    }


def main():
    if len(sys.argv) < 2:
        return 2
    report_path = Path(sys.argv[1]).resolve()
    try:
        report = {'status': 'pass', 'checks': run_check()}
        status = 0
    except BaseException as error:
        report = {'status': 'fail', 'error': str(error), 'traceback': traceback.format_exc()}
        status = 1
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return status


if __name__ == '__main__':
    raise SystemExit(main())
