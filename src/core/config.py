"""应用配置管理"""
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppConfig:
    """全局应用配置"""

    # 应用信息
    app_name: str = "文件大助"
    app_version: str = "1.0.0"

    # 最近使用的文件
    recent_pdf_files: list[str] = field(default_factory=list)
    recent_table_files: list[str] = field(default_factory=list)

    # 导出设置
    default_export_dir: str = os.path.expanduser("~/Desktop")
    auto_open_after_export: bool = True

    # 预览设置
    preview_row_limit: int = 100

    # 主题: "system" | "light" | "dark"
    theme: str = "system"

    # 语言
    language: str = "zh_CN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "recent_pdf_files": self.recent_pdf_files[-20:],
            "recent_table_files": self.recent_table_files[-20:],
            "default_export_dir": self.default_export_dir,
            "auto_open_after_export": self.auto_open_after_export,
            "preview_row_limit": self.preview_row_limit,
            "theme": self.theme,
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        return cls(
            app_name=data.get("app_name", "文件大助"),
            app_version=data.get("app_version", "1.0.0"),
            recent_pdf_files=data.get("recent_pdf_files", []),
            recent_table_files=data.get("recent_table_files", []),
            default_export_dir=data.get("default_export_dir", os.path.expanduser("~/Desktop")),
            auto_open_after_export=data.get("auto_open_after_export", True),
            preview_row_limit=data.get("preview_row_limit", 100),
            theme=data.get("theme", "system"),
            language=data.get("language", "zh_CN"),
        )

    @classmethod
    def config_dir(cls) -> Path:
        """配置文件目录"""
        path = Path.home() / ".file_assistant"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def config_file(cls) -> Path:
        """配置文件路径"""
        return cls.config_dir() / "config.json"

    @classmethod
    def load(cls) -> "AppConfig":
        """从磁盘加载配置"""
        config_file = cls.config_file()
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls.from_dict(data)
            except Exception:
                pass
        return cls()

    def save(self):
        """保存配置到磁盘"""
        config_file = self.config_file()
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
