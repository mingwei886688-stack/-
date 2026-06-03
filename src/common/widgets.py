"""公共 UI 组件 — 极简原生风格"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QFileDialog,
    QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont


# ─── 文件拖放区 ────────────────────────────────────

class DropZone(QFrame):
    """文件拖放区域"""

    files_dropped = Signal(list)

    def __init__(
        self,
        label: str = "拖拽文件到此处",
        description: str = "或点击选择文件",
        accepted_extensions: list[str] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._accepted_extensions = accepted_extensions or []

        self.setFrameShape(QFrame.Shape.Box)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)

        icon_label = QLabel("📂")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = icon_label.font(); f.setPointSize(28); icon_label.setFont(f)

        self._label = QLabel(label)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lf = self._label.font(); lf.setPointSize(14); self._label.setFont(lf)

        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        df = desc_label.font(); df.setPointSize(11); desc_label.setFont(df)

        layout.addWidget(icon_label)
        layout.addWidget(self._label)
        layout.addWidget(desc_label)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls]
        if self._accepted_extensions:
            file_paths = [f for f in file_paths
                          if os.path.splitext(f)[1].lower() in self._accepted_extensions]
        if file_paths:
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()

    def mousePressEvent(self, event):
        if self._accepted_extensions:
            ext_filter = f"支持的文件 ({' '.join('*' + e for e in self._accepted_extensions)})"
        else:
            ext_filter = ""
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", ext_filter)
        if file_paths:
            self.files_dropped.emit(file_paths)


# ─── 预览表格 ───────────────────────────────────────

class PreviewTable(QFrame):
    """表格预览组件"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table)

    def load_data(self, headers: list[str], rows: list[list], max_rows: int = 100):
        display_rows = rows[:max_rows]
        self._table.clear()
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setRowCount(len(display_rows))
        for r, row in enumerate(display_rows):
            for c, value in enumerate(row[:len(headers)]):
                item = QTableWidgetItem(str(value) if value is not None else "")
                self._table.setItem(r, c, item)
        self._table.resizeColumnsToContents()

    def clear(self):
        self._table.clear()
        self._table.setRowCount(0)
        self._table.setColumnCount(0)


# ─── 信息卡片 ───────────────────────────────────────

class InfoCard(QFrame):
    """信息展示卡片 — 原生简洁"""

    def __init__(self, title: str, value: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(72)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        self._title_label = QLabel(title)
        tf = self._title_label.font(); tf.setPointSize(11); self._title_label.setFont(tf)

        self._value_label = QLabel(value)
        vf = self._value_label.font(); vf.setPointSize(22); vf.setBold(True); self._value_label.setFont(vf)

        layout.addWidget(self._title_label)
        layout.addWidget(self._value_label)

    def set_value(self, value: str):
        self._value_label.setText(value)


# ─── 操作按钮栏 ─────────────────────────────────────

class ActionBar(QFrame):
    """底部操作栏"""

    preview_clicked = Signal()
    export_clicked = Signal()
    reset_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMaximumHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)

        self._hint_label = QLabel("")
        hf = self._hint_label.font(); hf.setPointSize(11); self._hint_label.setFont(hf)
        layout.addWidget(self._hint_label)
        layout.addStretch()

        self._reset_btn = QPushButton("🔄 重置")
        self._reset_btn.clicked.connect(self.reset_clicked.emit)
        layout.addWidget(self._reset_btn)

        self._preview_btn = QPushButton("👁 预览")
        self._preview_btn.clicked.connect(self.preview_clicked.emit)
        layout.addWidget(self._preview_btn)

        self._export_btn = QPushButton("📤 导出")
        self._export_btn.clicked.connect(self.export_clicked.emit)
        layout.addWidget(self._export_btn)

    def set_hint(self, text: str):
        self._hint_label.setText(text)

    def set_export_enabled(self, enabled: bool):
        self._export_btn.setEnabled(enabled)

    def set_preview_enabled(self, enabled: bool):
        self._preview_btn.setEnabled(enabled)
