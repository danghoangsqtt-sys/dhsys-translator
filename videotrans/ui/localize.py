"""Translate static labels in legacy dialogs that predate the locale catalog."""

from PySide6.QtWidgets import (
    QAbstractButton, QGroupBox, QLabel, QLineEdit, QPlainTextEdit,
    QTextEdit, QWidget,
)

from videotrans.configure.config import defaulelang, tr


def _translated(value):
    if not value or value.lstrip().startswith('<'):
        return value
    return tr(value)


def localize_widget_tree(window):
    if defaulelang != 'vi_VN' or window is None:
        return
    for widget in [window, *window.findChildren(QWidget)]:
        if widget.isWindow() and widget.windowTitle():
            widget.setWindowTitle(_translated(widget.windowTitle()))
        if isinstance(widget, (QAbstractButton, QLabel, QGroupBox)):
            value = widget.text() if hasattr(widget, 'text') else widget.title()
            translated = _translated(value)
            if translated != value:
                if isinstance(widget, QGroupBox):
                    widget.setTitle(translated)
                else:
                    widget.setText(translated)
        if isinstance(widget, (QLineEdit, QPlainTextEdit, QTextEdit)):
            value = widget.placeholderText()
            translated = _translated(value)
            if translated != value:
                widget.setPlaceholderText(translated)
        if widget.toolTip():
            widget.setToolTip(_translated(widget.toolTip()))
