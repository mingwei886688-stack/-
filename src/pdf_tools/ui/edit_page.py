"""PDF 编辑页面 UI"""
import io
import os
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QScrollArea,
    QFrame, QGridLayout, QDialog, QDialogButtonBox,
    QLineEdit, QSpinBox, QDoubleSpinBox, QFormLayout,
    QColorDialog, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QImage, QColor, QPalette

from common.widgets import ActionBar, InfoCard
from pdf_tools.editor import PDFEditor


# ─── 文字编辑弹窗 ────────────────────────────────

class TextEditDialog(QDialog):
    """文字编辑弹窗 — 添加或遮盖文字"""

    def __init__(self, mode: str, page_num: int, parent=None):
        """
        Args:
            mode: "add" 添加文字 或 "redact" 遮盖文字
            page_num: 页码 (1-based 显示用)
        """
        super().__init__(parent)
        self._mode = mode
        self.setWindowTitle(f"{'添加文字' if mode == 'add' else '遮盖/移除文字'} — 第 {page_num + 1} 页")
        self.setMinimumWidth(380)
        self.setModal(True)

        layout = QFormLayout(self)
        layout.setSpacing(12)

        if mode == "add":
            self._text_edit = QLineEdit()
            self._text_edit.setPlaceholderText("请输入要添加的文字")
            layout.addRow("文字内容:", self._text_edit)

            self._font_size = QSpinBox()
            self._font_size.setRange(8, 72)
            self._font_size.setValue(16)
            layout.addRow("字号:", self._font_size)

            self._x_spin = QDoubleSpinBox()
            self._x_spin.setRange(0, 1000)
            self._x_spin.setValue(50)
            self._x_spin.setDecimals(0)
            layout.addRow("X 坐标 (从左到右):", self._x_spin)

            self._y_spin = QDoubleSpinBox()
            self._y_spin.setRange(0, 1000)
            self._y_spin.setValue(700)
            self._y_spin.setDecimals(0)
            layout.addRow("Y 坐标 (从下到上):", self._y_spin)

        else:
            self._x_spin = QDoubleSpinBox()
            self._x_spin.setRange(0, 1000)
            self._x_spin.setValue(50)
            self._x_spin.setDecimals(0)
            layout.addRow("区域 X (从左到右):", self._x_spin)

            self._y_spin = QDoubleSpinBox()
            self._y_spin.setRange(0, 1000)
            self._y_spin.setValue(700)
            self._y_spin.setDecimals(0)
            layout.addRow("区域 Y (从下到上):", self._y_spin)

            self._width_spin = QDoubleSpinBox()
            self._width_spin.setRange(10, 1000)
            self._width_spin.setValue(200)
            self._width_spin.setDecimals(0)
            layout.addRow("遮盖宽度:", self._width_spin)

            self._height_spin = QDoubleSpinBox()
            self._height_spin.setRange(10, 1000)
            self._height_spin.setValue(30)
            self._height_spin.setDecimals(0)
            layout.addRow("遮盖高度:", self._height_spin)

            self._color_btn = QPushButton("白色 #FFFFFF")
            self._color_btn.clicked.connect(self._pick_color)
            layout.addRow("遮盖颜色:", self._color_btn)
            self._fill_color = "#FFFFFF"

        # 提示信息
        hint = QLabel(
            "💡 提示：PDF 页面坐标原点在左下角，\n"
            "X 向右增大，Y 向上增大。默认 A4 = 595×842"
        )
        hf = hint.font(); hf.setPointSize(10); hint.setFont(hf); hint.setStyleSheet("margin-top: 12px;")
        layout.addRow("", hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow("", buttons)

    def _pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self._fill_color = color.name()
            self._color_btn.setText(f"{self._fill_color}")

    def get_add_params(self) -> dict:
        return {
            "text": self._text_edit.text(),
            "font_size": self._font_size.value(),
            "x": self._x_spin.value(),
            "y": self._y_spin.value(),
        }

    def get_redact_params(self) -> dict:
        return {
            "x": self._x_spin.value(),
            "y": self._y_spin.value(),
            "width": self._width_spin.value(),
            "height": self._height_spin.value(),
            "fill_color": self._fill_color,
        }


# ─── 可选中页面缩略图 ──────────────────────────────

class PageThumbnail(QPushButton):
    """单个页面的缩略图按钮 — 显示真实PDF内容和页码"""

    toggled_page = Signal(int, bool)  # page_num, selected

    def __init__(self, page_num: int, parent=None):
        super().__init__(parent)
        self._page_num = page_num
        self.setCheckable(True)
        self.setFixedSize(180, 240)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"第 {page_num + 1} 页 — 点击选中")
        self.toggled.connect(lambda checked: self.toggled_page.emit(self._page_num, checked))

    def set_thumbnail(self, pixmap: QPixmap):
        """设置缩略图"""
        scaled = pixmap.scaled(
            172, 200, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setIcon(scaled)
        self.setIconSize(QSize(172, 200))

        # 在按钮下方显示页码
        self.setText(f"第 {self._page_num + 1} 页")
        self.setStyleSheet(self._thumb_style(False))

    def set_selected_style(self, selected: bool):
        self.setStyleSheet(self._thumb_style(selected))

    def _thumb_style(self, selected: bool) -> str:
        border_color = "#007aff" if selected else "#e5e5ea"
        bg = "#cce4ff" if selected else "#f9f9fb"
        return f"""
            QPushButton {{
                border: 2px solid {border_color};
                border-radius: 8px;
                background-color: {bg};
                font-size: 11px;
                font-weight: {"bold" if selected else "normal"};
                color: #1d1d1f;
            }}
            QPushButton:hover {{
                border-color: #007aff;
                background-color: #e8f0fe;
            }}
        """

    @property
    def page_num(self) -> int:
        return self._page_num


# ─── PDF 编辑页面 ─────────────────────────────────

class PDFEditPage(QWidget):
    """PDF 编辑工作区"""

    status_message = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._editor = PDFEditor()
        self._selected_pages: set[int] = set()
        self._thumbnails: list[PageThumbnail] = []
        self._is_dark = False

        self._setup_ui()
        self._connect_signals()

    def set_dark_mode(self, dark: bool):
        self._is_dark = dark
        self._page_count_card.set_dark_mode(dark)
        self._selected_count_card.set_dark_mode(dark)
        self._action_bar.set_dark_mode(dark)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(12)

        # ─── 标题 ───────────────────────
        title = QLabel("PDF 编辑")
        tf = title.font(); tf.setPointSize(20); tf.setBold(True); title.setFont(tf)
        desc = QLabel("打开 PDF，点击选中页面后可删除、旋转、提取、重排，或对页面添加/遮盖文字")
        df = desc.font(); df.setPointSize(12); desc.setFont(df)
        main_layout.addWidget(title)
        main_layout.addWidget(desc)

        # ─── 打开文件区 ────────────────
        open_frame = QFrame()
        open_layout = QHBoxLayout(open_frame)
        open_layout.setContentsMargins(0, 0, 0, 0)

        self._open_btn = QPushButton("📂 打开 PDF 文件")
        self._open_btn.setObjectName("primaryButton")
        self._open_btn.setMinimumWidth(180)

        self._file_label = QLabel("尚未打开文件")
        ff = self._file_label.font(); ff.setPointSize(13); self._file_label.setFont(ff)
        self._file_label.setWordWrap(True)

        open_layout.addWidget(self._open_btn)
        open_layout.addWidget(self._file_label)
        open_layout.addStretch()
        main_layout.addWidget(open_frame)

        # ─── 信息 + 操作按钮行 ────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self._page_count_card = InfoCard("总页数", "--")
        self._selected_count_card = InfoCard("已选页数", "0")
        top_row.addWidget(self._page_count_card)
        top_row.addWidget(self._selected_count_card)

        top_row.addSpacing(20)

        # 页面操作按钮
        self._delete_btn = QPushButton("🗑 删除选中页")
        self._delete_btn.setObjectName("secondaryButton")
        self._rotate_90_btn = QPushButton("↻ 旋转90°")
        self._rotate_90_btn.setObjectName("secondaryButton")
        self._rotate_180_btn = QPushButton("↻ 旋转180°")
        self._rotate_180_btn.setObjectName("secondaryButton")
        self._rotate_270_btn = QPushButton("↺ 旋转270°")
        self._rotate_270_btn.setObjectName("secondaryButton")
        self._extract_btn = QPushButton("✂ 提取选中页")
        self._extract_btn.setObjectName("secondaryButton")
        self._select_all_btn = QPushButton("☑ 全选/取消")
        self._select_all_btn.setObjectName("secondaryButton")

        top_row.addWidget(self._delete_btn)
        top_row.addWidget(self._rotate_90_btn)
        top_row.addWidget(self._rotate_180_btn)
        top_row.addWidget(self._rotate_270_btn)
        top_row.addWidget(self._extract_btn)
        top_row.addWidget(self._select_all_btn)
        top_row.addStretch()

        # 文字编辑按钮
        self._add_text_btn = QPushButton("➕ 添加文字")
        self._add_text_btn.setObjectName("secondaryButton")
        self._redact_btn = QPushButton("🖊 遮盖文字")
        self._redact_btn.setObjectName("secondaryButton")
        top_row.addWidget(self._add_text_btn)
        top_row.addWidget(self._redact_btn)

        main_layout.addLayout(top_row)

        # ─── 缩略图网格（滚动） ──────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._thumbnail_container = QWidget()
        self._thumbnail_layout = QGridLayout(self._thumbnail_container)
        self._thumbnail_layout.setSpacing(10)
        self._thumbnail_layout.setContentsMargins(0, 8, 0, 8)
        scroll.setWidget(self._thumbnail_container)

        self._placeholder = QLabel(
            "📂 打开 PDF 文件后将在此显示每页内容缩略图\n\n"
            "• 点击页面可选中\n"
            "• 按住 ⌘ 可多选\n"
            "• 选中后可删除、旋转、提取\n"
            "• 选中后可添加或遮盖文字"
        )
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pf = self._placeholder.font(); pf.setPointSize(14); self._placeholder.setFont(pf)
        self._placeholder.setStyleSheet("padding: 80px; color: #8e8e93;")
        self._thumbnail_layout.addWidget(self._placeholder, 0, 0)

        main_layout.addWidget(scroll)

        # ─── 底部操作栏 ──────────────────
        self._action_bar = ActionBar()
        self._action_bar.set_hint("编辑完成后点击保存")
        self._action_bar.set_preview_enabled(False)
        self._action_bar.set_export_enabled(False)
        self._action_bar._export_btn.setText("💾 保存")
        try:
            self._action_bar._export_btn.clicked.disconnect()
        except RuntimeError:
            pass
        self._action_bar._export_btn.clicked.connect(self._on_save)
        main_layout.addWidget(self._action_bar)

        self._update_action_states()

    def _connect_signals(self):
        self._open_btn.clicked.connect(self._on_open)
        self._delete_btn.clicked.connect(self._on_delete)
        self._rotate_90_btn.clicked.connect(lambda: self._on_rotate(90))
        self._rotate_180_btn.clicked.connect(lambda: self._on_rotate(180))
        self._rotate_270_btn.clicked.connect(lambda: self._on_rotate(270))
        self._extract_btn.clicked.connect(self._on_extract)
        self._select_all_btn.clicked.connect(self._on_select_all)
        self._add_text_btn.clicked.connect(self._on_add_text)
        self._redact_btn.clicked.connect(self._on_redact)
        self._action_bar.reset_clicked.connect(self._on_close)

    # ─── 文件加载 ───────────────────────

    def _on_open(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开 PDF 文件", "", "PDF 文件 (*.pdf)"
        )
        if file_path:
            self._load_pdf(file_path)

    def _load_pdf(self, file_path: str):
        if not self._editor.load(file_path):
            QMessageBox.critical(self, "打开失败", "无法读取 PDF 文件，文件可能已损坏。")
            return

        self._file_label.setText(f"📄 {os.path.basename(file_path)} ({self._editor.total_pages} 页)")
        self._page_count_card.set_value(str(self._editor.total_pages))
        self._selected_pages.clear()
        self._selected_count_card.set_value("0")
        self._render_thumbnails(file_path)
        self._action_bar.set_export_enabled(True)
        self._update_action_states()
        self.status_message.emit(f"✅ 已打开: {os.path.basename(file_path)}")

    # ─── 缩略图渲染 ──────────────────────

    def _render_thumbnails(self, file_path: str):
        """使用 pypdfium2 渲染真实 PDF 页面缩略图"""
        # 清除旧内容
        while self._thumbnail_layout.count():
            item = self._thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._thumbnails.clear()

        total = self._editor.total_pages
        if total == 0:
            self._placeholder = QLabel("该 PDF 没有页面")
            self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._thumbnail_layout.addWidget(self._placeholder, 0, 0)
            return

        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(file_path)

            cols = 5
            for i in range(total):
                # 渲染页面缩略图
                page = pdf[i]
                bitmap = page.render(scale=0.25)  # 缩放渲染
                pil_image = bitmap.to_pil()

                # 将 PIL Image 转为 QPixmap
                data = pil_image.convert("RGB").tobytes("raw", "RGB")
                qimage = QImage(data, pil_image.width, pil_image.height,
                               pil_image.width * 3, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)

                # 创建缩略图按钮
                thumb = PageThumbnail(i)
                thumb.set_thumbnail(pixmap)
                thumb.toggled_page.connect(self._on_thumb_toggled)
                self._thumbnails.append(thumb)

                self._thumbnail_layout.addWidget(thumb, i // cols, i % cols)

            pdf.close()
        except ImportError:
            # 降级：使用简单文字按钮
            cols = 5
            for i in range(total):
                thumb = PageThumbnail(i)
                # 不设置图片，只显示页码
                thumb.setText(f"第 {i+1} 页\n\n(预览不可用)")
                thumb.setFixedSize(180, 240)
                thumb.toggled_page.connect(self._on_thumb_toggled)
                self._thumbnails.append(thumb)
                self._thumbnail_layout.addWidget(thumb, i // cols, i % cols)

    def _on_thumb_toggled(self, page_num: int, selected: bool):
        if selected:
            self._selected_pages.add(page_num)
        else:
            self._selected_pages.discard(page_num)
        self._selected_count_card.set_value(str(len(self._selected_pages)))

        # 更新对应缩略图的样式
        for thumb in self._thumbnails:
            if thumb.page_num == page_num:
                thumb.set_selected_style(selected)
                break
        self._update_action_states()

    # ─── 页面操作 ───────────────────────

    def _on_delete(self):
        if not self._selected_pages:
            return
        count = len(self._selected_pages)
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除选中的 {count} 页吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            remaining = self._editor.delete_pages(list(self._selected_pages))
            self._selected_pages.clear()
            self._page_count_card.set_value(str(remaining))
            self._selected_count_card.set_value("0")
            self._file_label.setText(f"📄 {self._editor.file_name} ({remaining} 页)")
            self._refresh_file()
            self._update_action_states()
            self.status_message.emit(f"🗑 已删除 {count} 页，剩余 {remaining} 页")

    def _on_rotate(self, angle: int):
        if not self._selected_pages:
            return
        self._editor.rotate_pages(list(self._selected_pages), angle)
        self.status_message.emit(f"↻ 已将 {len(self._selected_pages)} 页旋转 {angle}°")
        self._refresh_file()

    def _on_extract(self):
        if not self._selected_pages:
            return
        output_path, _ = QFileDialog.getSaveFileName(
            self, "提取页面另存为", os.path.expanduser("~/Desktop/提取页面.pdf"),
            "PDF 文件 (*.pdf)"
        )
        if output_path:
            count = self._editor.extract_pages(list(self._selected_pages), output_path)
            self.status_message.emit(f"✂ 已提取 {count} 页到 {os.path.basename(output_path)}")
            reply = QMessageBox.question(
                self, "提取完成", f"已提取 {count} 页。\n\n打开文件所在目录？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                subprocess.run(["open", "-R", output_path])

    def _on_select_all(self):
        total = self._editor.total_pages
        if len(self._selected_pages) == total:
            self._selected_pages.clear()
        else:
            self._selected_pages = set(range(total))

        self._selected_count_card.set_value(str(len(self._selected_pages)))
        for thumb in self._thumbnails:
            in_selection = thumb.page_num in self._selected_pages
            thumb.setChecked(in_selection)
            thumb.set_selected_style(in_selection)
        self._update_action_states()

    # ─── 文字编辑 ───────────────────────

    def _on_add_text(self):
        """添加文字到选中页面"""
        if not self._selected_pages:
            QMessageBox.information(self, "提示",
                "请先在缩略图中选中要添加文字的页面（可多选）")
            return

        page_num = list(self._selected_pages)[0]
        dialog = TextEditDialog("add", page_num, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            params = dialog.get_add_params()
            if not params["text"].strip():
                QMessageBox.warning(self, "提示", "请输入文字内容")
                return

            for pg in self._selected_pages:
                self._editor.add_text(pg, params["text"], params["x"],
                                      params["y"], params["font_size"])
            self.status_message.emit(
                f"➕ 已在 {len(self._selected_pages)} 页添加文字: {params['text']}"
            )

    def _on_redact(self):
        """遮盖选中页面的文字"""
        if not self._selected_pages:
            QMessageBox.information(self, "提示",
                "请先在缩略图中选中要遮盖文字的页面（可多选）")
            return

        page_num = list(self._selected_pages)[0]
        dialog = TextEditDialog("redact", page_num, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            params = dialog.get_redact_params()
            for pg in self._selected_pages:
                self._editor.redact_text(pg, params["x"], params["y"],
                                         params["width"], params["height"],
                                         params["fill_color"])
            self.status_message.emit(
                f"🖊 已在 {len(self._selected_pages)} 页遮盖文字区域"
            )

    # ─── 保存 ───────────────────────────

    def _on_save(self):
        output_path, _ = QFileDialog.getSaveFileName(
            self, "保存 PDF", os.path.expanduser(f"~/Desktop/{self._editor.file_name}"),
            "PDF 文件 (*.pdf)"
        )
        if output_path:
            try:
                self._editor.save(output_path)
                self.status_message.emit(f"💾 已保存: {os.path.basename(output_path)}")
                reply = QMessageBox.question(
                    self, "保存成功", f"文件已保存。\n\n打开文件所在目录？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    subprocess.run(["open", "-R", output_path])
            except Exception as e:
                QMessageBox.critical(self, "保存失败", str(e))

    # ─── 辅助方法 ───────────────────────

    def _refresh_file(self):
        """刷新缩略图（旋转/删除后需要重新渲染）"""
        # 保存当前状态到临时文件再重新加载
        import tempfile
        fd, temp_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        try:
            self._editor.save(temp_path)
            # 重新加载
            old_selected = self._selected_pages.copy()
            self._editor.load(temp_path)
            self._selected_pages = {
                p for p in old_selected if p < self._editor.total_pages
            }
            self._render_thumbnails(temp_path)
            self._selected_count_card.set_value(str(len(self._selected_pages)))
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _update_action_states(self):
        has_file = self._editor.total_pages > 0
        has_selection = len(self._selected_pages) > 0

        self._delete_btn.setEnabled(has_selection)
        self._rotate_90_btn.setEnabled(has_selection)
        self._rotate_180_btn.setEnabled(has_selection)
        self._rotate_270_btn.setEnabled(has_selection)
        self._extract_btn.setEnabled(has_selection)
        self._select_all_btn.setEnabled(has_file)
        self._add_text_btn.setEnabled(has_selection)
        self._redact_btn.setEnabled(has_selection)
        self._action_bar.set_export_enabled(has_file)

    def _on_close(self):
        self._editor.close()
        self._selected_pages.clear()
        self._thumbnails.clear()
        self._file_label.setText("尚未打开文件")
        self._page_count_card.set_value("--")
        self._selected_count_card.set_value("0")
        self._action_bar.set_export_enabled(False)
        while self._thumbnail_layout.count():
            item = self._thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._placeholder = QLabel(
            "📂 打开 PDF 文件后将在此显示每页内容缩略图\n\n"
            "• 点击页面可选中\n"
            "• 按住 ⌘ 可多选\n"
            "• 选中后可删除、旋转、提取\n"
            "• 选中后可添加或遮盖文字"
        )
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pf = self._placeholder.font(); pf.setPointSize(14); self._placeholder.setFont(pf)
        self._placeholder.setStyleSheet("padding: 80px; color: #8e8e93;")
        self._thumbnail_layout.addWidget(self._placeholder, 0, 0)
        self._update_action_states()
        self.status_message.emit("🔄 已关闭文件")
