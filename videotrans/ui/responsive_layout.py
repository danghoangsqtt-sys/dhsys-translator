"""Small presentation layouts that adapt existing widgets to available width."""

from PySide6.QtCore import QPoint, QRect, QSize
from PySide6.QtWidgets import QLayout, QLayoutItem, QWidgetItem


class WrappingRowLayout(QLayout):
    """Lay out controls left-to-right and continue on the next line when needed.

    The layout intentionally owns no widgets. Existing rows can therefore keep
    their object names, settings bindings, and signal connections while their
    presentation adapts to a narrower workspace.
    """

    def __init__(self, parent=None, margin=0, spacing=8):
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def addItem(self, item):
        self._items.append(item)

    def addWidget(self, widget):
        self.addChildWidget(widget)
        self.addItem(QWidgetItem(widget))

    def addStretch(self, stretch=0):
        """Keep old row-builder calls harmless; wrapping rows do not use spacers."""
        return None

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        return size + QSize(left + right, top + bottom)

    def _item_size(self, item):
        hint = item.sizeHint()
        minimum = item.minimumSize()
        return QSize(max(hint.width(), minimum.width()), max(hint.height(), minimum.height()))

    def _layout(self, rect, measure_only):
        left, top, right, bottom = self.getContentsMargins()
        available = rect.adjusted(left, top, -right, -bottom)
        x, y = available.x(), available.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._items:
            widget = item.widget()
            if widget is not None and widget.isHidden():
                continue
            size = self._item_size(item)
            next_x = x + size.width()
            if line_height and next_x > available.right() + 1:
                x = available.x()
                y += line_height + spacing
                next_x = x + size.width()
                line_height = 0
            if not measure_only:
                item.setGeometry(QRect(QPoint(x, y), size))
            x = next_x + spacing
            line_height = max(line_height, size.height())

        return (y + line_height - rect.y()) + bottom
