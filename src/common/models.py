"""数据模型定义"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MergeMode(Enum):
    """表格合并模式"""
    VERTICAL = "垂直合并（追加行）"
    HORIZONTAL = "水平合并（追加列）"


class MatchMode(Enum):
    """匹配方式"""
    EXACT = "精确匹配"
    FUZZY = "模糊匹配"


@dataclass
class PDFFileInfo:
    """PDF 文件信息"""
    file_path: str = ""
    file_name: str = ""
    total_pages: int = 0
    selected_pages: str = ""  # 如 "1-5,8,10-12"，空表示全部
    thumbnail: Any = None     # 首页缩略图 QPixmap


@dataclass
class TableFileInfo:
    """表格文件信息"""
    file_path: str = ""
    file_name: str = ""
    sheet_names: list[str] = field(default_factory=list)
    selected_sheet: str = ""
    headers: list[str] = field(default_factory=list)
    row_count: int = 0
    preview_data: list[list[Any]] = field(default_factory=list)


@dataclass
class MatchPair:
    """表头匹配对"""
    source_column: str   # 源表列名
    lookup_column: str   # 查找表列名
