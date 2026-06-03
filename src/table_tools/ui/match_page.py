"""表头匹配页面 — 可视化 XLOOKUP"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox,
    QComboBox, QFrame, QScrollArea,
    QCheckBox, QGroupBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from common.widgets import PreviewTable, ActionBar
from table_tools.matcher import TableMatcher


def _l(text, size=12, bold=False):
    l = QLabel(text)
    f = l.font(); f.setPointSize(size); f.setBold(bold); l.setFont(f)
    return l


class HeaderCheckList(QFrame):
    """带复选框的列名列表"""
    selection_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checkboxes: dict[str, QCheckBox] = {}
        self._headers: list[str] = []

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(180)

        self._container = QWidget()
        self._clayout = QVBoxLayout(self._container)
        self._clayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._clayout.setContentsMargins(8, 6, 8, 6)
        self._clayout.setSpacing(2)
        scroll.setWidget(self._container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def set_headers(self, headers: list[str]):
        for cb in self._checkboxes.values():
            self._clayout.removeWidget(cb)
            cb.deleteLater()
        self._checkboxes.clear()
        self._headers = headers
        for h in headers:
            cb = QCheckBox(h)
            cb.toggled.connect(lambda: self.selection_changed.emit())
            self._checkboxes[h] = cb
            self._clayout.addWidget(cb)

    def get_checked(self) -> list[str]:
        return [h for h, cb in self._checkboxes.items() if cb.isChecked()]

    def clear(self):
        for cb in self._checkboxes.values():
            self._clayout.removeWidget(cb)
            cb.deleteLater()
        self._checkboxes.clear()
        self._headers = []


class MatchPairRow(QFrame):
    """一行匹配关系"""
    removed = Signal(object)

    def __init__(self, my_headers, ref_headers, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self); l.setContentsMargins(0, 2, 0, 2); l.setSpacing(6)

        l.addWidget(_l("把", 12))
        self._my_combo = QComboBox(); self._my_combo.addItems(my_headers); self._my_combo.setMinimumWidth(130)
        l.addWidget(self._my_combo)
        l.addWidget(_l("对应到", 12))
        self._ref_combo = QComboBox(); self._ref_combo.addItems(ref_headers); self._ref_combo.setMinimumWidth(130)
        l.addWidget(self._ref_combo)
        l.addWidget(_l("这一列", 12))

        rm = QPushButton("✕"); rm.setFixedSize(28, 28)
        rm.clicked.connect(lambda: self.removed.emit(self))
        l.addWidget(rm)
        l.addStretch()

    def get_pair(self): return (self._my_combo.currentText(), self._ref_combo.currentText())

    def update_headers(self, my_h, ref_h):
        a, b = self._my_combo.currentText(), self._ref_combo.currentText()
        self._my_combo.clear(); self._my_combo.addItems(my_h)
        if a in my_h: self._my_combo.setCurrentText(a)
        self._ref_combo.clear(); self._ref_combo.addItems(ref_h)
        if b in ref_h: self._ref_combo.setCurrentText(b)


class TableMatchPage(QWidget):
    """表头匹配工作区"""
    status_message = Signal(str)
    TABLE_EXTENSIONS = [".xlsx", ".xls", ".csv"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._matcher = TableMatcher()
        self._match_pairs_rows: list[MatchPairRow] = []
        self._my_key = ""
        self._ref_key = ""
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(12)

        # ─── 标题 ───
        main.addWidget(_l("表头匹配", 20, bold=True))

        # ─── 第1行：导入两个文件 ───
        row1 = QHBoxLayout(); row1.setSpacing(16)

        g1 = QGroupBox("📋 我的表格（需要补充数据的表）")
        g1l = QVBoxLayout(g1)
        h1 = QHBoxLayout()
        self._my_btn = QPushButton("📂 选择文件")
        self._my_file_label = QLabel("还没选文件")
        h1.addWidget(self._my_btn); h1.addWidget(self._my_file_label); h1.addStretch()
        g1l.addLayout(h1)
        self._my_sheet_combo = QComboBox(); self._my_sheet_combo.setVisible(False)
        self._my_sheet_combo.setPlaceholderText("选择 Sheet")
        g1l.addWidget(self._my_sheet_combo)
        row1.addWidget(g1)

        g2 = QGroupBox("📋 参考数据（要从中抄数据的表）")
        g2l = QVBoxLayout(g2)
        h2 = QHBoxLayout()
        self._ref_btn = QPushButton("📂 选择文件")
        self._ref_file_label = QLabel("还没选文件")
        h2.addWidget(self._ref_btn); h2.addWidget(self._ref_file_label); h2.addStretch()
        g2l.addLayout(h2)
        self._ref_sheet_combo = QComboBox(); self._ref_sheet_combo.setVisible(False)
        self._ref_sheet_combo.setPlaceholderText("选择 Sheet")
        g2l.addWidget(self._ref_sheet_combo)
        row1.addWidget(g2)

        main.addLayout(row1)

        # ─── 第2行：列名 + 匹配规则 ───
        row2 = QHBoxLayout(); row2.setSpacing(16)

        # 我的表格列名
        left_col = QVBoxLayout()
        left_col.addWidget(_l("我的表格有哪些列：", 12, bold=True))
        self._my_headers_list = HeaderCheckList()
        left_col.addWidget(self._my_headers_list)
        row2.addLayout(left_col)

        # 参考数据列名
        right_col = QVBoxLayout()
        right_col.addWidget(_l("参考数据有哪些列：", 12, bold=True))
        self._ref_headers_list = HeaderCheckList()
        right_col.addWidget(self._ref_headers_list)
        row2.addLayout(right_col)

        main.addLayout(row2)

        # ─── 第3行：匹配规则 + 要抄的列 ───
        g3 = QGroupBox("🔗 匹配规则设置")
        g3l = QVBoxLayout(g3); g3l.setSpacing(8)

        hint = _l("告诉工具哪两列是同一个意思（比如「姓名」=「员工姓名」），然后勾选要抄过来的列", 11)
        g3l.addWidget(hint)

        self._match_pairs_container = QVBoxLayout()
        g3l.addLayout(self._match_pairs_container)

        add_btn_row = QHBoxLayout()
        self._add_pair_btn = QPushButton("➕ 添加对应关系")
        add_btn_row.addWidget(self._add_pair_btn)
        add_btn_row.addStretch()
        g3l.addLayout(add_btn_row)

        # 要拉取的列
        pull_row = QHBoxLayout()
        pull_row.addWidget(_l("要抄过来的列（勾选）：", 12))
        self._match_mode_combo = QComboBox()
        self._match_mode_combo.addItems(["精确匹配", "模糊匹配"])
        pull_row.addWidget(self._match_mode_combo)
        pull_row.addStretch()
        g3l.addLayout(pull_row)

        self._pull_columns_list = HeaderCheckList()
        g3l.addWidget(self._pull_columns_list)

        main.addWidget(g3)

        # ─── 第4行：预览 ───
        main.addWidget(_l("匹配结果预览（前100行）", 12, bold=True))
        self._preview_table = PreviewTable()
        main.addWidget(self._preview_table)

        # ─── 底部操作栏 ───
        self._action_bar = ActionBar()
        self._action_bar.set_hint("导入两个文件 → 设对应关系 → 选要抄的列 → 预览 → 导出")
        self._action_bar.set_export_enabled(False)
        self._action_bar._preview_btn.setText("👁 预览结果")
        self._action_bar._export_btn.setText("📤 导出结果")
        main.addWidget(self._action_bar)

    def _connect_signals(self):
        self._my_btn.clicked.connect(lambda: self._on_select("my"))
        self._ref_btn.clicked.connect(lambda: self._on_select("ref"))
        self._my_sheet_combo.currentTextChanged.connect(lambda t: self._on_sheet("my", t))
        self._ref_sheet_combo.currentTextChanged.connect(lambda t: self._on_sheet("ref", t))
        self._add_pair_btn.clicked.connect(self._on_add_pair)
        self._action_bar.preview_clicked.connect(self._on_preview)
        self._action_bar.export_clicked.connect(self._on_export)
        self._action_bar.reset_clicked.connect(self._on_reset)

    def _on_select(self, tt):
        label_text = "我的表格" if tt == "my" else "参考数据"
        fp, _ = QFileDialog.getOpenFileName(self, f"选择{label_text}", "", "表格 (*.xlsx *.xls *.csv)")
        if not fp: return
        try:
            sheets = self._matcher.load_file(fp)
            combo = self._my_sheet_combo if tt == "my" else self._ref_sheet_combo
            label = self._my_file_label if tt == "my" else self._ref_file_label
            combo.clear(); combo.setVisible(True); combo.addItems(sheets)
            label.setText(f"✅ {os.path.basename(fp)}")
            label.setToolTip(fp)
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))

    def _on_sheet(self, tt, sn):
        if not sn: return
        label = self._my_file_label if tt == "my" else self._ref_file_label
        fp = label.toolTip()
        if not fp: return
        key = self._matcher.load_sheet(fp, sn)
        headers = self._matcher.get_headers(key)
        if tt == "my":
            self._my_key = key
            self._my_headers_list.set_headers(headers)
        else:
            self._ref_key = key
            self._ref_headers_list.set_headers(headers)
            self._pull_columns_list.set_headers(headers)
        self._update_combos()
        self._update_state()

    def _on_add_pair(self):
        mh = self._my_headers_list._headers
        rh = self._ref_headers_list._headers
        if not mh or not rh:
            self.status_message.emit("⚠ 请先导入两张表")
            return
        row = MatchPairRow(mh, rh)
        row.removed.connect(self._on_remove_pair)
        self._match_pairs_container.addWidget(row)
        self._match_pairs_rows.append(row)

    def _on_remove_pair(self, row):
        self._match_pairs_container.removeWidget(row)
        self._match_pairs_rows.remove(row)
        row.deleteLater()

    def _update_combos(self):
        for row in self._match_pairs_rows:
            row.update_headers(self._my_headers_list._headers, self._ref_headers_list._headers)

    def _update_state(self):
        can = bool(self._my_key and self._ref_key)
        self._action_bar.set_export_enabled(can)
        self._action_bar.set_preview_enabled(can)

    def _on_preview(self):
        try:
            self._run_match()
            if self._matcher._matched_result is not None:
                df = self._matcher._matched_result
                self._preview_table.load_data(list(df.columns), df.head(100).values.tolist())
                unmatched = self._matcher.get_unmatched_rows()
                self.status_message.emit(f"👁 共 {len(df)} 行，{len(unmatched)} 行未匹配")
                self._action_bar.set_export_enabled(True)
        except Exception as e:
            QMessageBox.warning(self, "匹配失败", str(e))

    def _run_match(self):
        pairs = [r.get_pair() for r in self._match_pairs_rows]
        if not pairs: raise ValueError("请至少添加一条对应关系")
        pull = self._pull_columns_list.get_checked()
        if not pull: raise ValueError("请至少勾选一列要抄过来的数据")
        self._matcher.set_match_config(
            source_key=self._my_key, lookup_key=self._ref_key,
            match_pairs=pairs, pull_columns=pull,
            match_mode="精确匹配" if "精确" in self._match_mode_combo.currentText() else "模糊匹配",
        )
        self._matcher.execute()

    def _on_export(self):
        if self._matcher._matched_result is None:
            return QMessageBox.warning(self, "提示", "请先预览结果")
        out, _ = QFileDialog.getSaveFileName(self, "导出", os.path.expanduser("~/Desktop/匹配结果.xlsx"),
                                              "Excel (*.xlsx);;CSV (*.csv)")
        if not out: return
        self._matcher.export(self._matcher._matched_result, out)
        QMessageBox.information(self, "完成", "匹配结果已导出！")
        self.status_message.emit(f"✅ 已导出: {os.path.basename(out)}")

    def _on_reset(self):
        self._matcher.clear()
        self._my_key = ""; self._ref_key = ""
        self._my_file_label.setText("还没选文件")
        self._ref_file_label.setText("还没选文件")
        self._my_sheet_combo.clear(); self._my_sheet_combo.setVisible(False)
        self._ref_sheet_combo.clear(); self._ref_sheet_combo.setVisible(False)
        self._my_headers_list.clear(); self._ref_headers_list.clear()
        self._pull_columns_list.clear()
        for row in self._match_pairs_rows:
            self._match_pairs_container.removeWidget(row); row.deleteLater()
        self._match_pairs_rows.clear()
        self._preview_table.clear()
        self._action_bar.set_export_enabled(False)
        self._action_bar.set_preview_enabled(False)
        self.status_message.emit("🔄 已重置")
