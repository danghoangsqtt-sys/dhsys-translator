from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QAbstractItemView


class DanspMixin:
    table_style_css="""
                QTableWidget {
                    background-color: #ffffff;
                    color: #17211c;
                    border: 1px solid #c9d5ce;
                    gridline-color: #e7ece9;
                }
                QTableWidget::item {
                    padding: 4px 6px;
                    border-bottom: 1px solid #e7ece9;
                }
                QTableWidget::item:selected {
                    background-color: #dcede4;
                    color: #0e3524;
                }
                QHeaderView::section {
                    background-color: #f1f5f2;
                    color: #244032;
                    border: 0;
                    border-bottom: 1px solid #c9d5ce;
                    padding: 5px;
                    font-weight: 700;
                }
                QPushButton#playBtn {
                    background-color: transparent;
                    color: #14452f;
                    border: none;
                    border-radius: 2px;
                    padding: 1px 4px;
                    min-width: 20px;
                    max-width: 24px;
                }
            """

    def configure_editable_subtitle_table(self):
        """Apply the shared, keyboard-accessible subtitle editor behavior."""
        self.table.setFocusPolicy(Qt.StrongFocus)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.SelectedClicked
            | QAbstractItemView.EditKeyPressed
            | QAbstractItemView.AnyKeyPressed
        )

    def set_subtitle_dirty(self, dirty=True):
        """Update the editor's dirty flag and its visible status label."""
        self.has_unsaved_changes = bool(dirty)
        label = getattr(self, "dirty_label", None)
        if label is None:
            return
        label.setProperty("dirty", self.has_unsaved_changes)
        label.setProperty("saveError", False)
        label.setText(self._dirty_text if self.has_unsaved_changes else self._clean_text)
        label.style().unpolish(label)
        label.style().polish(label)

    def show_subtitle_save_error(self):
        """Keep the dialog open and surface a failed SRT write."""
        label = getattr(self, "dirty_label", None)
        if label is None:
            return
        self.has_unsaved_changes = True
        label.setProperty("dirty", False)
        label.setProperty("saveError", True)
        label.setText(self._save_error_text)
        label.style().unpolish(label)
        label.style().polish(label)

        # --- 字号调整函数 ---
    def change_table_font_size(self, delta: int):
        # 1. 统一获取当前 pointSize
        font = self.table.font()
        current_pt = font.pointSize()

        # 容错：如果获取不到 pointSize，给一个合理的默认值（如 10）
        if current_pt <= 0:
            current_pt = 10

        # 计算新字号，限制最小为 6pt
        new_pt = max(6, current_pt + delta)
        font.setPointSize(new_pt)

        # 2. 统一将 QFont 应用给表格和表头
        self.table.setFont(font)
        if self.table.horizontalHeader():
            self.table.horizontalHeader().setFont(font)
        if self.table.verticalHeader():
            self.table.verticalHeader().setFont(font)

        # 3. 如果之前有单元格通过 item.setFont() 单独设置过字体，同步更新
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item_font = item.font()
                    item_font.setPointSize(new_pt)
                    item.setFont(item_font)

        # 4. 保存设置到 QSettings
        sets = QSettings("pyvideotrans", "settings")
        sets.setValue("danshipin_table_fontsize", new_pt)
