"""主窗口 — 左侧导航 + 右侧工作区（纯原生风格，无自定义样式表）"""
import sys
import subprocess
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QStatusBar,
    QFrame, QButtonGroup, QApplication, QSizePolicy,
    QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.config import AppConfig
from core.event_bus import bus, Events

from pdf_tools.ui.merge_page import PDFMergePage
from pdf_tools.ui.edit_page import PDFEditPage
from table_tools.ui.merge_page import TableMergePage
from table_tools.ui.match_page import TableMatchPage


class MainWindow(QMainWindow):
    """文件大助 — 使用原生系统控件，确保文字正常显示"""

    def __init__(self, config: AppConfig):
        super().__init__()
        self._config = config

        self.setWindowTitle(f"{config.app_name} v{config.app_version}")
        self.setMinimumSize(1100, 740)
        self.resize(1280, 820)

        self._setup_ui()
        self._setup_event_bus()

    def _nav_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setMinimumHeight(36)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return btn

    def _nav_label(self, text: str, is_title: bool = False) -> QLabel:
        label = QLabel(text)
        font = label.font()
        if is_title:
            font.setPointSize(18)
            font.setBold(True)
        else:
            font.setPointSize(12)
        label.setFont(font)
        return label

    def _nav_section(self, text: str) -> QLabel:
        label = QLabel(text)
        font = label.font()
        font.setPointSize(10)
        font.setBold(True)
        label.setFont(font)
        return label

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── 左侧导航栏 ──────────────────
        nav_panel = QFrame()
        nav_panel.setFixedWidth(220)
        nav_panel.setFrameShape(QFrame.Shape.StyledPanel)

        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(16, 20, 16, 20)
        nav_layout.setSpacing(4)

        nav_layout.addWidget(self._nav_label("📁 文件大助", is_title=True))
        nav_layout.addWidget(self._nav_label("办公杂项工具箱"))
        nav_layout.addSpacing(12)

        nav_layout.addWidget(self._nav_section("PDF 工具"))
        self._btn_pdf_merge = self._nav_btn("📄 PDF 合并")
        self._btn_pdf_edit = self._nav_btn("✏️ PDF 编辑")
        nav_layout.addWidget(self._btn_pdf_merge)
        nav_layout.addWidget(self._btn_pdf_edit)
        nav_layout.addSpacing(8)

        nav_layout.addWidget(self._nav_section("表格工具"))
        self._btn_table_merge = self._nav_btn("📊 表格合并")
        self._btn_table_match = self._nav_btn("🔗 表头匹配")
        nav_layout.addWidget(self._btn_table_merge)
        nav_layout.addWidget(self._btn_table_match)

        nav_layout.addStretch()

        version_label = QLabel(f"v{self._config.app_version}")
        vf = version_label.font()
        vf.setPointSize(10)
        version_label.setFont(vf)
        nav_layout.addWidget(version_label)

        # 导航按钮分组（互斥）
        self._nav_group = QButtonGroup()
        self._nav_group.addButton(self._btn_pdf_merge, 0)
        self._nav_group.addButton(self._btn_pdf_edit, 1)
        self._nav_group.addButton(self._btn_table_merge, 2)
        self._nav_group.addButton(self._btn_table_match, 3)
        self._nav_group.buttonClicked.connect(self._on_nav_clicked)

        # ─── 右侧工作区 ──────────────────
        self._workspace = QStackedWidget()

        self._pdf_merge_page = PDFMergePage()
        self._pdf_edit_page = PDFEditPage()
        self._table_merge_page = TableMergePage()
        self._table_match_page = TableMatchPage()

        self._workspace.addWidget(self._pdf_merge_page)     # 0
        self._workspace.addWidget(self._pdf_edit_page)       # 1
        self._workspace.addWidget(self._table_merge_page)    # 2
        self._workspace.addWidget(self._table_match_page)    # 3

        self._btn_pdf_merge.setChecked(True)
        self._workspace.setCurrentIndex(0)

        main_layout.addWidget(nav_panel)
        main_layout.addWidget(self._workspace, 1)

        # ─── 状态栏 ──────────────────────
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("就绪")

    def _on_nav_clicked(self, button):
        index = self._nav_group.id(button)
        self._workspace.setCurrentIndex(index)
        names = {0: "PDF 合并", 1: "PDF 编辑", 2: "表格合并", 3: "表头匹配"}
        self._status_bar.showMessage(f"已切换到: {names.get(index, '')}")

    def _setup_event_bus(self):
        for page in [
            self._pdf_merge_page, self._pdf_edit_page,
            self._table_merge_page, self._table_match_page,
        ]:
            page.status_message.connect(self._show_status)

    def _show_status(self, message: str):
        self._status_bar.showMessage(message, 5000)

    def closeEvent(self, event):
        self._config.save()
        super().closeEvent(event)
