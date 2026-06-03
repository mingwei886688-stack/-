#!/usr/bin/env python3
"""文件大助 — 桌面办公工具箱"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from core.config import AppConfig
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("文件大助")
    app.setApplicationVersion("1.0.0")

    # 设置默认字体（原生系统字体，不强制指定避免渲染问题）
    font = QFont()
    font.setPointSize(13)
    app.setFont(font)

    config = AppConfig.load()
    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
