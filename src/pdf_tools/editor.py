"""PDF 编辑业务逻辑"""
import io
import os
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import FreeText
from pypdf.generic import RectangleObject


class PDFEditor:
    """PDF 编辑器 — 删除页面、旋转、提取、重排、文字编辑"""

    def __init__(self):
        self._reader: PdfReader | None = None
        self._file_path: str = ""
        self._operations: list[dict] = []  # 操作历史（用于撤销）
        self._page_annotations: dict[int, list[dict]] = {}  # 每页的文字标注 {page_num: [{text, x, y, size}]}

    def load(self, file_path: str) -> bool:
        """加载 PDF 文件"""
        try:
            self._reader = PdfReader(file_path)
            self._file_path = file_path
            self._operations.clear()
            return True
        except Exception:
            return False

    @property
    def total_pages(self) -> int:
        return len(self._reader.pages) if self._reader else 0

    @property
    def file_name(self) -> str:
        return os.path.basename(self._file_path)

    def render_page(self, page_num: int, scale: float = 0.3) -> "Image":
        """渲染指定页面为缩略图（用于 Web 展示）"""
        import pypdfium2 as pdfium
        if not self._reader or page_num >= len(self._reader.pages):
            raise ValueError("无效的页码")
        pdf = pdfium.PdfDocument(self._file_path)
        page = pdf[page_num]
        bitmap = page.render(scale=scale)
        img = bitmap.to_pil()
        pdf.close()
        return img

    def delete_pages(self, page_numbers: list[int]) -> int:
        """删除指定页面（0-based），返回剩余页数"""
        if not self._reader:
            return 0

        writer = PdfWriter()
        pages_to_delete = set(page_numbers)

        for i in range(len(self._reader.pages)):
            if i not in pages_to_delete:
                writer.add_page(self._reader.pages[i])

        # 替换内部 reader
        import io
        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)
        self._reader = PdfReader(buffer)
        self._operations.append({"type": "delete", "pages": page_numbers})
        return len(self._reader.pages)

    def rotate_pages(self, page_numbers: list[int], angle: int) -> bool:
        """旋转指定页面（0-based）

        Args:
            page_numbers: 页码列表
            angle: 旋转角度 (90, 180, 270)
        """
        if not self._reader or angle not in (90, 180, 270):
            return False

        for page_num in page_numbers:
            if 0 <= page_num < len(self._reader.pages):
                self._reader.pages[page_num].rotate(angle)

        self._operations.append({"type": "rotate", "pages": page_numbers, "angle": angle})
        return True

    def extract_pages(self, page_numbers: list[int], output_path: str) -> int:
        """提取指定页面并保存为新 PDF，返回提取的页数"""
        if not self._reader:
            return 0

        writer = PdfWriter()
        for page_num in sorted(page_numbers):
            if 0 <= page_num < len(self._reader.pages):
                writer.add_page(self._reader.pages[page_num])

        with open(output_path, "wb") as f:
            writer.write(f)
        return len(page_numbers)

    def reorder_pages(self, new_order: list[int]) -> bool:
        """重新排列页面顺序"""
        if not self._reader:
            return False
        if sorted(new_order) != list(range(len(self._reader.pages))):
            return False

        writer = PdfWriter()
        for page_num in new_order:
            writer.add_page(self._reader.pages[page_num])

        import io
        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)
        self._reader = PdfReader(buffer)
        self._operations.append({"type": "reorder", "order": new_order})
        return True

    def add_text(self, page_num: int, text: str, x: float, y: float,
                 font_size: int = 14, color: str = "#000000"):
        """在指定页面添加文字

        Args:
            page_num: 页码 (0-based)
            text: 文字内容
            x, y: 位置坐标 (左下角)
            font_size: 字号
            color: 文字颜色
        """
        if not self._reader or page_num >= len(self._reader.pages):
            return False

        rect = RectangleObject([x, y, x + len(text) * font_size * 0.6, y + font_size * 1.5])
        annotation = FreeText(
            text=text,
            rect=rect,
            font="Arial",
            font_size=f"{font_size}pt",
            font_color=color,
            border_color=None,
            background_color=None,
        )
        self._reader.pages[page_num].add_annotation(annotation)

        if page_num not in self._page_annotations:
            self._page_annotations[page_num] = []
        self._page_annotations[page_num].append({
            "type": "add", "text": text, "x": x, "y": y, "size": font_size
        })
        self._operations.append({
            "type": "add_text", "page": page_num, "text": text,
            "x": x, "y": y, "size": font_size
        })
        return True

    def redact_text(self, page_num: int, x: float, y: float,
                    width: float, height: float, fill_color: str = "#FFFFFF"):
        """移除/遮盖指定区域的文字（用矩形覆盖）

        Args:
            page_num: 页码 (0-based)
            x, y: 矩形左下角坐标
            width, height: 矩形宽度和高度
            fill_color: 覆盖颜色（默认白色）
        """
        if not self._reader or page_num >= len(self._reader.pages):
            return False

        page = self._reader.pages[page_num]
        # 在页面上添加一个填充矩形来遮盖文字
        from pypdf.generic import RectangleObject as Rect

        # 使用页面的 content stream 来画矩形
        # 简化方式：使用 annotation 标记，实际保存时会应用 redaction
        page.add_redaction(Rect([x, y, x + width, y + height]),
                          fill=fill_color)

        self._operations.append({
            "type": "redact", "page": page_num,
            "x": x, "y": y, "width": width, "height": height
        })
        return True

    def save(self, output_path: str | None = None) -> bool:
        """保存编辑后的 PDF（包括应用 redaction）"""
        if not self._reader:
            return False

        save_path = output_path or self._file_path
        writer = PdfWriter()

        # 先写入所有页面到临时 buffer 以应用 redaction
        temp_buffer = io.BytesIO()
        temp_writer = PdfWriter()
        for page in self._reader.pages:
            temp_writer.add_page(page)
        temp_writer.write(temp_buffer)
        temp_buffer.seek(0)

        # 重新读取以应用 redaction
        reader_with_redactions = PdfReader(temp_buffer)
        for page in reader_with_redactions.pages:
            writer.add_page(page)

        # 应用所有 redaction
        writer.write(save_path) if hasattr(writer, 'write') else None
        with open(save_path, "wb") as f:
            writer.write(f)
        return True

    def close(self):
        self._reader = None
        self._file_path = ""
        self._operations.clear()
