"""表头匹配引擎 — 可视化 XLOOKUP"""
import os
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum


class MatchMode(Enum):
    EXACT = "精确匹配"
    FUZZY = "模糊匹配"


@dataclass
class MatchConfig:
    """匹配配置"""
    source_key: str = ""         # 源表 key
    lookup_key: str = ""         # 查找表 key
    match_pairs: list[tuple[str, str]] = field(default_factory=list)
    # [(源表列名, 查找表列名), ...]
    pull_columns: list[str] = field(default_factory=list)
    # 要从查找表拉取的列名
    match_mode: MatchMode = MatchMode.EXACT
    keep_unmatched: bool = True


class TableMatcher:
    """表头匹配引擎"""

    def __init__(self):
        self._dataframes: dict[str, pd.DataFrame] = {}
        self._file_info: dict[str, dict] = {}
        self._match_config = MatchConfig()
        self._matched_result: pd.DataFrame | None = None

    def load_file(self, file_path: str, sheet_name: str | None = None) -> list[str]:
        """加载表格文件，返回 Sheet 名称列表"""
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
            return xls.sheet_names

        return []

    def load_sheet(self, file_path: str, sheet_name: str) -> str:
        """加载指定 Sheet，返回 key"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            return list(self._dataframes.keys())[-1] if self._dataframes else ""

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
        """获取数据框的列名"""
        if key in self._dataframes:
            return list(self._dataframes[key].columns)
        return []

    def set_match_config(
        self,
        source_key: str,
        lookup_key: str,
        match_pairs: list[tuple[str, str]],
        pull_columns: list[str],
        match_mode: str = "精确匹配",
    ):
        """配置匹配参数"""
        self._match_config = MatchConfig(
            source_key=source_key,
            lookup_key=lookup_key,
            match_pairs=match_pairs,
            pull_columns=pull_columns,
            match_mode=MatchMode.EXACT if match_mode == "精确匹配" else MatchMode.FUZZY,
        )

    def execute(self) -> pd.DataFrame:
        """执行匹配

        Returns:
            匹配后的 DataFrame
        """
        config = self._match_config
        source_df = self._dataframes.get(config.source_key)
        lookup_df = self._dataframes.get(config.lookup_key)

        if source_df is None or lookup_df is None:
            raise ValueError("源表或查找表未加载")

        # 构建 merge 参数
        left_on = [pair[0] for pair in config.match_pairs]
        right_on = [pair[1] for pair in config.match_pairs]

        if config.match_mode == MatchMode.FUZZY:
            return self._fuzzy_match(source_df, lookup_df, config)

        # 精确匹配
        # 只保留查找表中需要的列（匹配键 + 拉取列）
        lookup_cols = right_on + [c for c in config.pull_columns if c not in right_on]
        lookup_cols = [c for c in lookup_cols if c in lookup_df.columns]

        result = source_df.merge(
            lookup_df[lookup_cols],
            left_on=left_on,
            right_on=right_on,
            how="left" if config.keep_unmatched else "inner",
            suffixes=("", "_查找表"),
        )

        # 去重匹配键列（保留源表的）
        for l, r in zip(left_on, right_on):
            if l == r:
                if r + "_查找表" in result.columns:
                    result.drop(columns=[r + "_查找表"], inplace=True)

        self._matched_result = result
        return result

    def _fuzzy_match(
        self, source_df: pd.DataFrame, lookup_df: pd.DataFrame, config: MatchConfig
    ) -> pd.DataFrame:
        """模糊匹配（简单的字符串包含判断）"""
        result = source_df.copy()

        for pull_col in config.pull_columns:
            result[pull_col] = None

        for idx, row in result.iterrows():
            for _, l_row in lookup_df.iterrows():
                match = True
                for src_col, lkp_col in config.match_pairs:
                    src_val = str(row[src_col]).lower().strip()
                    lkp_val = str(l_row[lkp_col]).lower().strip()
                    if src_val not in lkp_val and lkp_val not in src_val:
                        match = False
                        break
                if match:
                    for pull_col in config.pull_columns:
                        if pull_col in lookup_df.columns:
                            result.at[idx, pull_col] = l_row[pull_col]
                    break

        self._matched_result = result
        return result

    def get_unmatched_rows(self) -> pd.DataFrame:
        """获取未匹配到的行"""
        if self._matched_result is None:
            return pd.DataFrame()

        config = self._match_config
        unmatched_mask = pd.Series(False, index=self._matched_result.index)

        for pull_col in config.pull_columns:
            if pull_col in self._matched_result.columns:
                unmatched_mask |= self._matched_result[pull_col].isna()

        return self._matched_result[unmatched_mask]

    def export(self, df: pd.DataFrame, output_path: str):
        """导出结果"""
        ext = os.path.splitext(output_path)[1].lower()
        if ext == ".csv":
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
        elif ext in (".xlsx", ".xls"):
            df.to_excel(output_path, index=False)
        else:
            df.to_excel(output_path + ".xlsx", index=False)

    def clear(self):
        self._dataframes.clear()
        self._file_info.clear()
        self._matched_result = None
        self._match_config = MatchConfig()

    @property
    def loaded_keys(self) -> list[str]:
        return list(self._dataframes.keys())

    def get_key_by_label(self, file_name: str, sheet_name: str) -> str:
        return f"{file_name}::{sheet_name}"

    def get_info(self, key: str) -> dict:
        return self._file_info.get(key, {})
