"""表格合并业务逻辑"""
import os
import pandas as pd
from pathlib import Path


class TableMerger:
    """表格合并器 — 支持多文件/多Sheet的垂直与水平合并"""

    def __init__(self):
        self._dataframes: dict[str, pd.DataFrame] = {}
        # key: "文件名::Sheet名"
        self._file_info: dict[str, dict] = {}

    def load_file(self, file_path: str, sheet_name: str | None = None) -> list[str]:
        """加载表格文件，返回所有 Sheet 名称列表

        Args:
            file_path: 文件路径
            sheet_name: 指定 Sheet 名称，None 则返回全部 Sheet 列表

        Returns:
            Sheet 名称列表
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".csv":
            df = pd.read_csv(file_path)
            key = f"{os.path.basename(file_path)}::Sheet1"
            self._dataframes[key] = df
            self._file_info[key] = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "sheet_name": "Sheet1",
                "headers": list(df.columns),
                "row_count": len(df),
            }
            return ["Sheet1"]

        elif ext in (".xlsx", ".xls"):
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names

            if sheet_name and sheet_name in sheet_names:
                # 加载指定 sheet
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                key = f"{os.path.basename(file_path)}::{sheet_name}"
                self._dataframes[key] = df
                self._file_info[key] = {
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "sheet_name": sheet_name,
                    "headers": list(df.columns),
                    "row_count": len(df),
                }
            elif not sheet_name:
                # 返回所有 sheet 名称，不实际加载
                pass

            return sheet_names
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

    def load_sheet(self, file_path: str, sheet_name: str) -> str:
        """加载指定 Sheet

        Returns:
            数据框的 key
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            return self.load_file(file_path)[0]

        df = pd.read_excel(file_path, sheet_name=sheet_name)
        key = f"{os.path.basename(file_path)}::{sheet_name}"
        self._dataframes[key] = df
        self._file_info[key] = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "sheet_name": sheet_name,
            "headers": list(df.columns),
            "row_count": len(df),
        }
        return key

    def get_headers(self, key: str) -> list[str]:
        """获取某个数据框的列名"""
        if key in self._dataframes:
            return list(self._dataframes[key].columns)
        return []

    def get_preview(self, key: str, rows: int = 100) -> list[list]:
        """获取数据预览"""
        if key in self._dataframes:
            df = self._dataframes[key].head(rows)
            return [df.columns.tolist()] + df.values.tolist()
        return []

    def merge_vertical(self, keys: list[str], align_by: str = "name") -> pd.DataFrame:
        """垂直合并（追加行）

        将所有选中的数据框按列名对齐后纵向拼接。

        Args:
            keys: 要合并的数据框 key 列表
            align_by: 对齐方式 "name"（按列名）或 "position"（按位置）

        Returns:
            合并后的 DataFrame
        """
        if not keys:
            raise ValueError("未选择要合并的表格")

        dfs = [self._dataframes[k] for k in keys if k in self._dataframes]

        if align_by == "name":
            # 按列名对齐并追加
            all_columns = []
            for df in dfs:
                for col in df.columns:
                    if col not in all_columns:
                        all_columns.append(col)

            aligned = []
            for df in dfs:
                temp = df.copy()
                for col in all_columns:
                    if col not in temp.columns:
                        temp[col] = None
                temp = temp[all_columns]
                aligned.append(temp)
            return pd.concat(aligned, ignore_index=True)
        else:
            return pd.concat(dfs, ignore_index=True)

    def merge_horizontal(self, keys: list[str]) -> pd.DataFrame:
        """水平合并（追加列）

        将选中的数据框横向拼接。
        """
        if not keys:
            raise ValueError("未选择要合并的表格")

        dfs = [self._dataframes[k] for k in keys if k in self._dataframes]
        return pd.concat(dfs, axis=1)

    def export(self, df: pd.DataFrame, output_path: str):
        """导出 DataFrame 到文件"""
        ext = os.path.splitext(output_path)[1].lower()
        if ext == ".csv":
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
        elif ext in (".xlsx", ".xls"):
            df.to_excel(output_path, index=False)
        else:
            df.to_excel(output_path + ".xlsx", index=False)

    def remove(self, key: str):
        """移除某个数据框"""
        self._dataframes.pop(key, None)
        self._file_info.pop(key, None)

    def clear(self):
        """清空所有数据"""
        self._dataframes.clear()
        self._file_info.clear()

    @property
    def loaded_keys(self) -> list[str]:
        return list(self._dataframes.keys())
