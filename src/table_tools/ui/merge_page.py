"""表格合并页面"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox,
    QFrame, QScrollArea,
    QCheckBox, QRadioButton,
)
from PySide6.QtCore import Qt, Signal

from common.widgets import DropZone, PreviewTable
from table_tools.merger import TableMerger


class SheetCheckItem(QFrame):
    """单个 Sheet 复选框条目"""
    toggled = Signal(str, bool)  # key, checked

    def __init__(self, key: str, label: str, info: str = "", parent=None):
        super().__init__(parent)
        self._key = key
        self.setFrameShape(QFrame.Shape.Box)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self._check = QCheckBox(label)
        cf = self._check.font(); cf.setPointSize(12); self._check.setFont(cf)
        self._check.toggled.connect(lambda checked: self.toggled.emit(self._key, checked))
        layout.addWidget(self._check)

        self._info_label = QLabel(info)
        inf = self._info_label.font(); inf.setPointSize(10); self._info_label.setFont(inf)
        layout.addWidget(self._info_label)
        layout.addStretch()

    @property
    def key(self): return self._key

    def is_checked(self): return self._check.isChecked()

    def set_checked(self, v: bool): self._check.setChecked(v)


class TableMergePage(QWidget):
    status_message = Signal(str)
    TABLE_EXTENSIONS = [".xlsx", ".xls", ".csv"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._merger = TableMerger()
        self._sheet_items: dict[str, SheetCheckItem] = {}
        self._setup_ui()
        self._connect_signals()

    def _title(self, t, size=20):
        l = QLabel(t); f = l.font(); f.setPointSize(size); f.setBold(True); l.setFont(f); return l

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(12)

        main.addWidget(self._title("表格合并"))
        desc = QLabel("勾选要合并的 Sheet，支持垂直追加（并排）或水平拼接（并列）")
        df = desc.font(); df.setPointSize(12); desc.setFont(df)
        main.addWidget(desc)

        # 拖放区
        self._drop_zone = DropZone(
            label="拖拽表格文件到此处",
            description="支持 .xlsx / .xls / .csv（可多选文件）",
            accepted_extensions=self.TABLE_EXTENSIONS,
        )
        main.addWidget(self._drop_zone)

        # Sheet 选择列表
        main.addWidget(self._title("选择要合并的 Sheet", 14))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(150)
        self._sheet_container = QWidget()
        self._sheet_layout = QVBoxLayout(self._sheet_container)
        self._sheet_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._sheet_layout.setContentsMargins(0, 0, 0, 0)
        self._sheet_layout.setSpacing(4)
        scroll.setWidget(self._sheet_container)
        main.addWidget(scroll)

        # 操作按钮行
        btn_row = QHBoxLayout()
        self._select_all_btn = QPushButton("☑ 全选")
        self._deselect_all_btn = QPushButton("☐ 取消全选")
        self._remove_checked_btn = QPushButton("🗑 移除已选")
        self._clear_all_btn = QPushButton("✕ 清空全部")
        btn_row.addWidget(self._select_all_btn)
        btn_row.addWidget(self._deselect_all_btn)
        btn_row.addWidget(self._remove_checked_btn)
        btn_row.addWidget(self._clear_all_btn)
        btn_row.addStretch()
        main.addLayout(btn_row)

        # 合并模式
        mode_row = QHBoxLayout()
        mode_row.addWidget(self._title("合并模式：", 12))
        self._vertical_radio = QRadioButton("垂直合并（追加行）— 相同列名对齐后纵向拼接")
        self._vertical_radio.setChecked(True)
        self._horizontal_radio = QRadioButton("水平合并（追加列）— 按行索引横向拼接")
        mode_row.addWidget(self._vertical_radio)
        mode_row.addWidget(self._horizontal_radio)
        mode_row.addStretch()
        main.addLayout(mode_row)

        # 信息行
        info_row = QHBoxLayout()
        self._info_label = QLabel("已选: 0 个 Sheet  |  合计: 0 行")
        infof = self._info_label.font(); infof.setPointSize(12); self._info_label.setFont(infof)
        info_row.addWidget(self._info_label)
        info_row.addStretch()
        main.addLayout(info_row)

        # 预览
        main.addWidget(self._title("合并预览（前100行）", 12))
        self._preview_table = PreviewTable()
        main.addWidget(self._preview_table)

        # 底部按钮
        btn2 = QHBoxLayout()
        btn2.addStretch()
        self._preview_btn = QPushButton("👁 预览")
        self._export_btn = QPushButton("📤 合并导出")
        self._export_btn.setEnabled(False)
        btn2.addWidget(self._preview_btn)
        btn2.addWidget(self._export_btn)
        main.addLayout(btn2)

    def _connect_signals(self):
        self._drop_zone.files_dropped.connect(self._on_files_dropped)
        self._select_all_btn.clicked.connect(lambda: self._toggle_all(True))
        self._deselect_all_btn.clicked.connect(lambda: self._toggle_all(False))
        self._remove_checked_btn.clicked.connect(self._on_remove_checked)
        self._clear_all_btn.clicked.connect(self._on_clear_all)
        self._preview_btn.clicked.connect(self._on_preview)
        self._export_btn.clicked.connect(self._on_export)

    def _on_files_dropped(self, file_paths):
        new_count = 0
        for fp in file_paths:
            try:
                fname = os.path.basename(fp)
                # 获取 Sheet 列表
                sheets = self._merger.load_file(fp)
                for sn in sheets:
                    key = f"{fname}::{sn}"
                    if key in self._sheet_items:
                        continue
                    # 实际加载数据
                    self._merger.load_sheet(fp, sn)
                    info = self._merger._file_info.get(key, {})
                    rows = info.get("row_count", 0)
                    cols = len(info.get("headers", []))
                    label = f"{fname}  →  {sn}"
                    info_text = f"({rows} 行 × {cols} 列)"
                    item = SheetCheckItem(key, label, info_text)
                    item.toggled.connect(self._on_item_toggled)
                    self._sheet_layout.addWidget(item)
                    self._sheet_items[key] = item
                    new_count += 1
            except Exception as e:
                self.status_message.emit(f"⚠ {os.path.basename(fp)}: {e}")
        if new_count > 0:
            self.status_message.emit(f"✅ 已添加 {new_count} 个 Sheet")
        else:
            self.status_message.emit("⚠ 未发现新的 Sheet（可能已存在）")
        self._update_info()

    def _on_item_toggled(self, key, checked):
        self._update_info()

    def _toggle_all(self, checked):
        for item in self._sheet_items.values():
            item.set_checked(checked)
        self._update_info()

    def _on_remove_checked(self):
        to_remove = [k for k, item in self._sheet_items.items() if item.is_checked()]
        for k in to_remove:
            self._sheet_layout.removeWidget(self._sheet_items[k])
            self._sheet_items[k].deleteLater()
            del self._sheet_items[k]
            self._merger.remove(k)
        self._update_info()

    def _on_clear_all(self):
        for item in list(self._sheet_items.values()):
            self._sheet_layout.removeWidget(item)
            item.deleteLater()
        self._sheet_items.clear()
        self._merger.clear()
        self._preview_table.clear()
        self._export_btn.setEnabled(False)
        self._update_info()
        self.status_message.emit("🔄 已清空")

    def _update_info(self):
        checked = [k for k, item in self._sheet_items.items() if item.is_checked()]
        total_rows = 0
        for k in checked:
            total_rows += self._merger._file_info.get(k, {}).get("row_count", 0)
        self._info_label.setText(f"已选: {len(checked)} 个 Sheet  |  合计: {total_rows} 行")
        self._export_btn.setEnabled(len(checked) >= 2)

    def _get_checked_keys(self):
        return [k for k, item in self._sheet_items.items() if item.is_checked()]

    def _on_preview(self):
        keys = self._get_checked_keys()
        if len(keys) < 2:
            self.status_message.emit("⚠ 请至少勾选 2 个 Sheet 再预览")
            return
        try:
            if self._vertical_radio.isChecked():
                merged = self._merger.merge_vertical(keys)
            else:
                merged = self._merger.merge_horizontal(keys)
            self._preview_table.load_data(list(merged.columns), merged.head(100).values.tolist())
            self.status_message.emit(f"👁 合并结果: {len(merged)} 行 × {len(merged.columns)} 列")
        except Exception as e:
            QMessageBox.warning(self, "预览失败", str(e))

    def _on_export(self):
        keys = self._get_checked_keys()
        if len(keys) < 2:
            return
        out, _ = QFileDialog.getSaveFileName(
            self, "保存合并结果", os.path.expanduser("~/Desktop/合并表格.xlsx"),
            "Excel (*.xlsx);;CSV (*.csv)"
        )
        if not out:
            return
        try:
            if self._vertical_radio.isChecked():
                merged = self._merger.merge_vertical(keys)
            else:
                merged = self._merger.merge_horizontal(keys)
            self._merger.export(merged, out)
            QMessageBox.information(self, "完成", f"已导出 {len(merged)} 行")
            self.status_message.emit(f"✅ 已导出: {os.path.basename(out)}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))
