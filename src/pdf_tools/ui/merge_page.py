"""PDF 合并页面"""
import os
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QSplitter,
    QFrame, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from common.widgets import DropZone
from pdf_tools.merger import PDFMerger


class PDFMergePage(QWidget):
    status_message = Signal(str)
    PDF_EXTENSIONS = [".pdf"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._merger = PDFMerger()
        self._setup_ui()
        self._connect_signals()

    def _title(self, text: str) -> QLabel:
        l = QLabel(text)
        f = l.font(); f.setPointSize(20); f.setBold(True); l.setFont(f)
        return l

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(12)

        main.addWidget(self._title("PDF 合并"))
        desc = QLabel("将多个 PDF 文件合并为一个，支持拖拽排序和选择页面范围")
        df = desc.font(); df.setPointSize(12); desc.setFont(df)
        main.addWidget(desc)

        self._drop_zone = DropZone(
            label="拖拽 PDF 文件到此处",
            description="或点击选择文件（支持多选）",
            accepted_extensions=self.PDF_EXTENSIONS,
        )
        main.addWidget(self._drop_zone)

        # 文件列表
        list_label = QLabel("已导入文件（选中后点移除）")
        lf = list_label.font(); lf.setPointSize(12); lf.setBold(True); list_label.setFont(lf)
        main.addWidget(list_label)

        self._file_list = QListWidget()
        self._file_list.setAlternatingRowColors(True)
        self._file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._file_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        main.addWidget(self._file_list)

        btn_row = QHBoxLayout()
        self._remove_btn = QPushButton("🗑 移除选中")
        self._clear_btn = QPushButton("✕ 清空列表")
        btn_row.addWidget(self._remove_btn)
        btn_row.addWidget(self._clear_btn)
        btn_row.addStretch()
        main.addLayout(btn_row)

        # 信息行
        info_row = QHBoxLayout()
        self._count_label = QLabel("文件数量: 0")
        self._pages_label = QLabel("总页数: 0")
        info_row.addWidget(self._count_label)
        info_row.addWidget(self._pages_label)
        info_row.addStretch()
        main.addLayout(info_row)

        # 合并导出按钮
        self._merge_btn = QPushButton("📤 合并导出")
        self._merge_btn.setEnabled(False)
        self._merge_btn.setMinimumHeight(40)
        main.addWidget(self._merge_btn)

    def _connect_signals(self):
        self._drop_zone.files_dropped.connect(self._on_files_dropped)
        self._remove_btn.clicked.connect(self._on_remove)
        self._clear_btn.clicked.connect(self._on_clear)
        self._merge_btn.clicked.connect(self._on_merge)

    def _on_files_dropped(self, file_paths: list[str]):
        pdf_files = [f for f in file_paths if f.lower().endswith(".pdf")]
        if not pdf_files:
            self.status_message.emit("⚠ 未检测到 PDF 文件")
            return
        for fp in pdf_files:
            if fp not in self._merger.file_paths:
                self._merger.add_file(fp)
                self._file_list.addItem(os.path.basename(fp))
        self._update_info()
        self.status_message.emit(f"✅ 已添加 {len(pdf_files)} 个文件")

    def _on_remove(self):
        for item in self._file_list.selectedItems():
            row = self._file_list.row(item)
            self._file_list.takeItem(row)
            self._merger.remove_file(row)
        self._update_info()

    def _on_clear(self):
        self._merger.clear()
        self._file_list.clear()
        self._update_info()
        self.status_message.emit("🔄 已清空")

    def _update_info(self):
        count = self._merger.file_count
        self._count_label.setText(f"文件数量: {count}")
        total = sum(self._merger.get_file_info(i).get("total_pages", 0) for i in range(count))
        self._pages_label.setText(f"总页数: {total}")
        self._merge_btn.setEnabled(count > 0)

    def _on_merge(self):
        if self._merger.file_count == 0:
            return
        output_path, _ = QFileDialog.getSaveFileName(
            self, "保存合并 PDF", os.path.expanduser("~/Desktop/合并文档.pdf"),
            "PDF 文件 (*.pdf)"
        )
        if not output_path:
            return
        try:
            total = self._merger.merge(output_path)
            QMessageBox.information(self, "完成", f"合并成功！共 {total} 页。")
            subprocess.run(["open", "-R", output_path])
            self.status_message.emit(f"✅ 合并完成: {total} 页")
        except Exception as e:
            QMessageBox.critical(self, "合并失败", str(e))
