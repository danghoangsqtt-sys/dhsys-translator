"""Wizard step 2: languages, voice, subtitle style, a cost summary and Advanced."""

from typing import Callable, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from videotrans.configure._i18n import tr
from videotrans.ui.wizard.adapter import CheckMirror, ComboMirror
from videotrans.ui.wizard.step_video import TILE_STYLE, tile

# (subtitle_type, title key, hint key); values are the persisted enum.
SUBTITLE_TILES = (
    (1, "wizard_sub_hard", "wizard_sub_hard_hint"),
    (2, "wizard_sub_soft", "wizard_sub_soft_hint"),
    (3, "wizard_sub_bilingual", "wizard_sub_bilingual_hint"),
    (0, "wizard_sub_none", "wizard_sub_none_hint"),
)

ADVANCED_COMBOS = ("recogn_type", "model_name", "translate_type", "tts_type")
ADVANCED_CHECKS = ("voice_autorate", "video_autorate", "is_separate", "enable_cuda")


def cost_summary(adapter) -> str:
    """'0 đ · no API key' when every provider in use needs no key."""
    from videotrans.ui.provider_visibility import provider_access

    keyed = []
    for kind, provider_id in adapter.selected_providers():
        try:
            access = provider_access(kind, provider_id)
        except ValueError:
            continue
        if access.api_key_required:
            keyed.append(kind)
    if not keyed:
        return tr("wizard_cost_free")
    return tr("wizard_cost_key") + " " + ", ".join(tr(f"wizard_kind_{kind}") for kind in keyed)


def format_total(ms: int) -> str:
    seconds = max(0, int(ms) // 1000)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


class OptionsStep(QWidget):
    changed = Signal()

    def __init__(self, adapter, parent=None, *, total_duration: Optional[Callable[[], int]] = None,
                 video_count: Optional[Callable[[], int]] = None):
        super().__init__(parent)
        self.setObjectName("wizardOptionsStep")
        self.setStyleSheet(TILE_STYLE)
        self.adapter = adapter
        main = adapter.main
        self._total_duration = total_duration or (lambda: 0)
        self._video_count = video_count or (lambda: len(adapter.videos()))

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)
        # The left column scrolls so opening Advanced never squeezes the tiles.
        left_body = QWidget()
        left_body.setObjectName("wizardOptionsBody")
        left = QVBoxLayout(left_body)
        left.setContentsMargins(0, 0, 8, 0)
        left.setSpacing(12)

        languages = QFrame()
        languages.setObjectName("wizardLanguages")
        language_form = QGridLayout(languages)
        language_form.addWidget(QLabel(tr("wizard_source_language")), 0, 0)
        language_form.addWidget(QLabel(tr("wizard_target_language")), 0, 2)
        self.source_language = ComboMirror(main.source_language)
        self.target_language = ComboMirror(main.target_language)
        language_form.addWidget(self.source_language, 1, 0)
        language_form.addWidget(QLabel("→"), 1, 1)
        language_form.addWidget(self.target_language, 1, 2)
        self.target_hint = QLabel(tr("wizard_need_target"))
        self.target_hint.setObjectName("wizardNeedTarget")
        self.target_hint.setStyleSheet("color:#8a5a00;")
        language_form.addWidget(self.target_hint, 2, 0, 1, 3)
        left.addWidget(self._section(tr("wizard_languages"), languages))

        self.voice_box = QFrame()
        voice_row = QHBoxLayout(self.voice_box)
        voice_row.setContentsMargins(0, 0, 0, 0)
        self.voice_role = ComboMirror(main.voice_role)
        self.voice_role.setMinimumWidth(260)
        voice_row.addWidget(self.voice_role, 1)
        self.preview_button = QPushButton(tr("wizard_preview_voice"))
        self.preview_button.setObjectName("wizardPreviewVoice")
        self.preview_button.clicked.connect(adapter.preview_voice)
        voice_row.addWidget(self.preview_button)
        self.voice_section = self._section(tr("wizard_voice"), self.voice_box)
        left.addWidget(self.voice_section)

        tiles = QWidget()
        grid = QGridLayout(tiles)
        grid.setContentsMargins(0, 0, 0, 0)
        self.subtitle_group = QButtonGroup(self)
        self.subtitle_group.setExclusive(True)
        self.subtitle_buttons = {}
        for position, (value, title_key, hint_key) in enumerate(SUBTITLE_TILES):
            button = tile(tr(title_key), tr(hint_key))
            button.setObjectName(f"wizardSubtitle_{value}")
            button.clicked.connect(lambda _checked=False, v=value: main.subtitle_type.setCurrentIndex(v))
            self.subtitle_group.addButton(button)
            self.subtitle_buttons[value] = button
            grid.addWidget(button, position // 2, position % 2)
        self.subtitle_section = self._section(tr("wizard_subtitles"), tiles)
        left.addWidget(self.subtitle_section)

        self.advanced_toggle = QToolButton()
        self.advanced_toggle.setObjectName("wizardAdvancedToggle")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setText(tr("wizard_advanced"))
        self.advanced_toggle.toggled.connect(self._toggle_advanced)
        left.addWidget(self.advanced_toggle)
        self.advanced = QFrame()
        self.advanced.setObjectName("wizardAdvanced")
        advanced_form = QFormLayout(self.advanced)
        self.advanced_combos = {}
        for name in ADVANCED_COMBOS:
            source = getattr(main, name, None)
            if source is None:
                continue
            mirror = ComboMirror(source)
            self.advanced_combos[name] = mirror
            advanced_form.addRow(tr(f"wizard_adv_{name}"), mirror)
        self.advanced_checks = {}
        for name in ADVANCED_CHECKS:
            source = getattr(main, name, None)
            if source is None:
                continue
            mirror = CheckMirror(source)
            self.advanced_checks[name] = mirror
            advanced_form.addRow(mirror)
        self.all_options = QPushButton(tr("wizard_all_options"))
        self.all_options.setObjectName("wizardAllOptions")
        self.all_options.clicked.connect(adapter.show_classic_workspace)
        advanced_form.addRow(self.all_options)
        self.advanced.hide()
        left.addWidget(self.advanced)
        left.addStretch(1)
        self.scroll = QScrollArea()
        self.scroll.setObjectName("wizardOptionsScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidget(left_body)
        root.addWidget(self.scroll, 3)

        summary = QFrame()
        summary.setObjectName("wizardSummary")
        summary.setStyleSheet("QFrame#wizardSummary { background:#f4f6f5; border:1px solid #d9e0dc; border-radius:10px; }")
        summary_layout = QVBoxLayout(summary)
        heading = QLabel(tr("wizard_summary"))
        heading.setStyleSheet("font-size:15px;font-weight:600;")
        summary_layout.addWidget(heading)
        self.summary = QLabel()
        self.summary.setObjectName("wizardSummaryText")
        self.summary.setWordWrap(True)
        summary_layout.addWidget(self.summary)
        self.cost = QLabel()
        self.cost.setObjectName("wizardCost")
        self.cost.setWordWrap(True)
        self.cost.setStyleSheet("font-weight:600;color:#14452f;")
        summary_layout.addWidget(self.cost)
        summary_layout.addStretch(1)
        root.addWidget(summary, 2)

        for source in (main.source_language, main.target_language, main.voice_role, main.subtitle_type,
                       main.recogn_type, main.translate_type, main.tts_type):
            source.currentIndexChanged.connect(self.refresh)
        self.refresh()

    @staticmethod
    def _section(title: str, body: QWidget) -> QFrame:
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(title)
        label.setStyleSheet("font-size:15px;font-weight:600;")
        layout.addWidget(label)
        layout.addWidget(body)
        return frame

    def _toggle_advanced(self, shown: bool):
        self.advanced.setVisible(shown)

    def is_ready(self) -> bool:
        return not self.adapter.needs_target_language() or self.adapter.target_language_set()

    def refresh(self, *_):
        main = self.adapter.main
        extract_only = not self.adapter.needs_target_language()
        self.target_hint.setVisible(not self.is_ready())
        self.voice_section.setVisible(not extract_only)
        self.subtitle_section.setVisible(not extract_only)
        dubbing = self.adapter.dubbing_enabled()
        self.preview_button.setEnabled(dubbing)
        current = main.subtitle_type.currentIndex()
        for value, button in self.subtitle_buttons.items():
            button.setChecked(value == current)

        lines = [
            f"{tr('wizard_summary_videos')}: {self._video_count()} · {format_total(self._total_duration())}",
            f"{tr('wizard_languages')}: {main.source_language.currentText()} → {main.target_language.currentText()}",
        ]
        if not extract_only:
            lines.append(f"{tr('wizard_voice')}: {main.voice_role.currentText() if dubbing else tr('wizard_no_dubbing')}")
            lines.append(f"{tr('wizard_subtitles')}: {main.subtitle_type.currentText()}")
        self.summary.setText("\n".join(lines))
        self.cost.setText(cost_summary(self.adapter))
        self.changed.emit()
