"""Bridge between the wizard pages and the classic main-window widgets.

``check_start`` and every existing handler read the classic widgets, so the
wizard changes those widgets instead of writing params: mirrors show synced
copies, and setting a mirror sets the source widget, which fires the existing
signal handlers (voice list refresh, model list refresh, provider profile...).
"""

from pathlib import Path
from typing import Iterable, List, Optional

from PySide6.QtWidgets import QCheckBox, QComboBox

from videotrans.ui.wizard.presets import (
    APP_MODE_EXTRACT,
    PurposeSettings,
    purpose_for,
    purpose_settings,
)


class ComboMirror(QComboBox):
    """A QComboBox that mirrors another combo's items, hidden rows and selection."""

    def __init__(self, source: QComboBox, parent=None):
        super().__init__(parent)
        self.source = source
        self.setObjectName(f"wizardMirror_{source.objectName() or 'combo'}")
        self.setToolTip(source.toolTip())
        self._syncing = False
        self.rebuild()
        model = source.model()
        for signal in (model.modelReset, model.rowsInserted, model.rowsRemoved, model.dataChanged):
            signal.connect(self.rebuild)
        source.currentIndexChanged.connect(self._from_source)
        self.currentIndexChanged.connect(self._to_source)

    def rebuild(self, *_):
        self._syncing = True
        try:
            self.clear()
            for row in range(self.source.count()):
                self.addItem(self.source.itemText(row))
                tooltip = self.source.itemData(row, 3)  # Qt.ToolTipRole
                if tooltip:
                    self.setItemData(row, tooltip, 3)
            self.sync_hidden_rows()
            self.setCurrentIndex(self.source.currentIndex())
            self.setEnabled(self.source.isEnabled())
        finally:
            self._syncing = False

    def sync_hidden_rows(self):
        source_view = self.source.view()
        for row in range(min(self.count(), self.source.count())):
            self.view().setRowHidden(row, source_view.isRowHidden(row))

    def _from_source(self, index):
        if self._syncing:
            return
        self._syncing = True
        try:
            if self.count() != self.source.count():
                self.rebuild()
            self.setCurrentIndex(index)
            self.setEnabled(self.source.isEnabled())
        finally:
            self._syncing = False

    def _to_source(self, index):
        if self._syncing or index < 0:
            return
        self._syncing = True
        try:
            self.source.setCurrentIndex(index)
        finally:
            self._syncing = False

    def showPopup(self):
        # Provider rows can be shown/hidden later through the show-all switch.
        self.sync_hidden_rows()
        self.setEnabled(self.source.isEnabled())
        super().showPopup()


class CheckMirror(QCheckBox):
    """A checkbox kept in sync with an existing checkbox."""

    def __init__(self, source: QCheckBox, parent=None):
        super().__init__(source.text(), parent)
        self.source = source
        self.setObjectName(f"wizardMirror_{source.objectName() or 'check'}")
        self.setToolTip(source.toolTip())
        self.setChecked(source.isChecked())
        source.toggled.connect(self._from_source)
        self.toggled.connect(self._to_source)

    def _from_source(self, checked):
        if self.isChecked() != checked:
            self.blockSignals(True)
            self.setChecked(checked)
            self.blockSignals(False)

    def _to_source(self, checked):
        if self.source.isChecked() != checked:
            self.source.setChecked(checked)


class MainWindowAdapter:
    """Everything the wizard needs from the classic main window, in one place."""

    def __init__(self, main):
        self.main = main

    @property
    def action(self):
        return getattr(self.main, "win_action", None)

    # ------------------------------------------------------------ videos
    def set_videos(self, paths: Iterable[str]):
        files = [Path(path).as_posix() for path in paths]
        if self.action is not None:
            self.action.queue_mp4 = list(files)
        source_label = getattr(self.main, "source_mp4", None)
        if source_label is not None:
            source_label.setText(f"{len(files)} videos" if files else "")

    def videos(self) -> List[str]:
        return list(getattr(self.action, "queue_mp4", []) or [])

    def output_dir(self) -> Optional[str]:
        return getattr(self.main, "target_dir", None) or None

    def set_output_dir(self, path: Optional[str]):
        self.main.target_dir = Path(path).as_posix() if path else None
        label = getattr(self.main, "output_dir", None)
        if label is not None and path:
            from videotrans.configure._i18n import tr
            label.setText(tr("Translation results saved to:") + self.main.target_dir)

    # ----------------------------------------------------------- purpose
    def current_purpose(self) -> str:
        return purpose_for(getattr(self.main, "app_mode", "biaozhun"), self.main.voice_role.currentText())

    def apply_purpose(self, purpose: str) -> PurposeSettings:
        settings = purpose_settings(purpose, self.main.subtitle_type.currentIndex())
        if self.action is not None:
            if settings.app_mode == APP_MODE_EXTRACT:
                self.action.set_tiquzimu()
            else:
                self.action.set_biaozhun()
        else:
            self.main.app_mode = settings.app_mode
        if settings.subtitle_type is not None:
            self.main.subtitle_type.setCurrentIndex(settings.subtitle_type)
        self._set_dubbing(settings.dubbing)
        return settings

    def _set_dubbing(self, enabled: bool):
        roles = self.main.voice_role
        if not enabled:
            index = roles.findText("No")
            if index >= 0:
                roles.setCurrentIndex(index)
            return
        if roles.currentText() not in ("", "No"):
            return
        for row in range(roles.count()):
            if roles.itemText(row) not in ("No", "clone", ""):
                roles.setCurrentIndex(row)
                return

    def needs_target_language(self) -> bool:
        return getattr(self.main, "app_mode", "biaozhun") != APP_MODE_EXTRACT

    def target_language_set(self) -> bool:
        return self.main.target_language.currentIndex() > 0

    # ------------------------------------------------------------- voice
    def preview_voice(self):
        if self.action is not None:
            self.action.listen_voice_fun()

    def dubbing_enabled(self) -> bool:
        return self.main.voice_role.currentText() not in ("", "No")

    # ----------------------------------------------------------- providers
    def selected_providers(self):
        """(kind, provider_id) pairs that the current job would actually use."""
        from videotrans.ui.provider_visibility import RECOGNITION, TRANSLATION, TTS

        used = [(RECOGNITION, self.main.recogn_type.currentIndex())]
        if self.target_language_set():
            used.append((TRANSLATION, self.main.translate_type.currentIndex()))
        if self.dubbing_enabled() and self.needs_target_language():
            used.append((TTS, self.main.tts_type.currentIndex()))
        return used

    def show_classic_workspace(self):
        handler = getattr(self.main, "show_workspace", None)
        if callable(handler):
            handler()

    # --------------------------------------------------------------- jobs
    def is_running(self) -> bool:
        from videotrans.configure.config import app_cfg

        return getattr(app_cfg, "current_status", "") == "ing"

    def start_job(self) -> bool:
        """Start through the classic check; True when it switched to running.

        The classic action creates its job list on a short timer, so callers
        read ``jobs()`` a moment later.
        """
        if self.action is None or self.is_running():
            return False
        self.action.check_start()
        return self.is_running()

    def stop_job(self):
        if self.action is not None and self.is_running():
            self.action.update_status("stop")

    def jobs(self):
        """(uuid, file name) for every job created by the last start."""
        return [(item["uuid"], item["name"] or "") for item in getattr(self.action, "obj_list", []) or []]
