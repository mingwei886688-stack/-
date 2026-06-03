"""PDF 合并业务逻辑"""
import os
import io
from pathlib import Path
from pypdf import PdfReader, PdfWriter


class PDFMerger:
    """PDF 合并器"""

    def __init__(self):
        self._readers: list[PdfReader] = []
        self._file_paths: list[str] = []
        self._page_ranges: dict[int, tuple[int, int] | None] = {}
        # page_ranges: {file_index: (start, end)} 或 None 表示全部

    def add_file(self, file_path: str):
        """添加 PDF 文件"""
        if file_path not in self._file_paths:
            self._file_paths.append(file_path)
            self._readers.append(PdfReader(file_path))

    def remove_file(self, index: int):
        """移除指定索引的文件"""
        if 0 <= index < len(self._file_paths):
            del self._file_paths[index]
            del self._readers[index]

    def set_page_range(self, file_index: int, start: int, end: int):
        """设置某个文件的页码范围（1-based，含两端）"""
        if 0 <= file_index < len(self._readers):
            total = len(self._readers[file_index].pages)
            start = max(1, start)
            end = min(total, end)
            self._page_ranges[file_index] = (start, end)

    def clear_page_range(self, file_index: int):
        """清除页码范围（使用全部页面）"""
        self._page_ranges.pop(file_index, None)

    def get_file_info(self, index: int) -> dict:
        """获取文件信息"""
        if 0 <= index < len(self._file_paths):
            reader = self._readers[index]
            return {
                "file_name": os.path.basename(self._file_paths[index]),
                "file_path": self._file_paths[index],
                "total_pages": len(reader.pages),
            }
        return {}

    def reorder_files(self, indices: list[int]):
        """重新排序文件"""
        if sorted(indices) != list(range(len(self._file_paths))):
            raise ValueError("排序索引不完整")
        self._file_paths = [self._file_paths[i] for i in indices]
        self._readers = [self._readers[i] for i in indices]

    def merge(self, output_path: str) -> int:
        """执行合并，返回总页数

        Args:
            output_path: 输出文件路径

        Returns:
            合并后的总页数
        """
        writer = PdfWriter()
        total_pages = 0

        for i, reader in enumerate(self._readers):
            page_range = self._page_ranges.get(i)
            if page_range:
                start, end = page_range
                # 转为 0-based
                for page_num in range(start - 1, end):
                    writer.add_page(reader.pages[page_num])
                    total_pages += 1
            else:
                for page in reader.pages:
                    writer.add_page(page)
                    total_pages += len(reader.pages)

        with open(output_path, "wb") as f:
            writer.write(f)

        return total_pages

    @property
    def file_count(self) -> int:
        return len(self._file_paths)

    @property
    def file_paths(self) -> list[str]:
        return self._file_paths.copy()

    def clear(self):
        self._readers.clear()
        self._file_paths.clear()
        self._page_ranges.clear()
