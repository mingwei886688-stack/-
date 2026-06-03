"""样式表 — 只控制颜色和背景，不干预字体和布局"""
from PySide6.QtCore import Qt


class ThemeManager:
    """主题管理器 — 提供轻量样式，不覆盖原生控件渲染"""

    @staticmethod
    def nav_panel_style(is_dark: bool = False) -> str:
        """左侧导航面板样式"""
        if is_dark:
            return """
                #navPanel {
                    background-color: #2c2c2e;
                    border-right: 1px solid #38383a;
                    min-width: 220px;
                    max-width: 220px;
                }
                #navTitle {
                    color: #ffffff;
                    padding: 20px 16px 8px 16px;
                }
                #navSubtitle {
                    color: #98989d;
                    padding: 0px 16px 12px 16px;
                }
                #navGroupLabel {
                    color: #98989d;
                    padding: 12px 16px 4px 16px;
                }
            """
        return """
            #navPanel {
                background-color: #ececf0;
                border-right: 1px solid #d1d1d6;
                min-width: 220px;
                max-width: 220px;
            }
            #navTitle {
                color: #1d1d1f;
                padding: 20px 16px 8px 16px;
            }
            #navSubtitle {
                color: #86868b;
                padding: 0px 16px 12px 16px;
            }
            #navGroupLabel {
                color: #86868b;
                padding: 12px 16px 4px 16px;
            }
        """

    @staticmethod
    def nav_button_style(is_dark: bool = False) -> str:
        """导航按钮样式"""
        light = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding: 10px 16px;
                margin: 2px 8px;
                color: #1d1d1f;
            }
            QPushButton:hover {
                background-color: #dcdce0;
            }
            QPushButton:checked {
                background-color: #007aff;
                color: white;
            }
        """
        dark = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding: 10px 16px;
                margin: 2px 8px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #3a3a3c;
            }
            QPushButton:checked {
                background-color: #0a84ff;
                color: white;
            }
        """
        return dark if is_dark else light

    @staticmethod
    def global_style(is_dark: bool = False) -> str:
        """全局主窗口样式 — 最小干预原则"""
        if is_dark:
            return """
                QMainWindow {
                    background-color: #1c1c1e;
                }
                QStatusBar {
                    background-color: #2c2c2e;
                    border-top: 1px solid #38383a;
                    color: #98989d;
                }
                #card {
                    background-color: #2c2c2e;
                    border: 1px solid #38383a;
                    border-radius: 10px;
                    padding: 16px;
                }
            """
        return """
            QMainWindow {
                background-color: #f5f5f7;
            }
            QStatusBar {
                background-color: #f5f5f7;
                border-top: 1px solid #d1d1d6;
                color: #86868b;
            }
            #card {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 10px;
                padding: 16px;
            }
        """

    @staticmethod
    def card_style(is_dark: bool = False) -> str:
        """卡片样式"""
        if is_dark:
            return """
                background-color: #2c2c2e;
                border: 1px solid #38383a;
                border-radius: 10px;
                padding: 16px;
            """
        return """
            background-color: #ffffff;
            border: 1px solid #e5e5ea;
            border-radius: 10px;
            padding: 16px;
        """

    @staticmethod
    def dropzone_style(is_dark: bool = False) -> str:
        """文件拖放区样式"""
        if is_dark:
            return """
                QFrame#dropZone {
                    background-color: #1c1c1e;
                    border: 2px dashed #48484a;
                    border-radius: 10px;
                    padding: 24px;
                    color: #98989d;
                }
            """
        return """
            QFrame#dropZone {
                background-color: #f9f9fb;
                border: 2px dashed #c7c7cc;
                border-radius: 10px;
                padding: 24px;
                color: #86868b;
            }
        """

    @staticmethod
    def button_style(is_dark: bool = False) -> str:
        """按钮样式（primary/secondary）"""
        if is_dark:
            return """
                QPushButton#primaryButton {
                    background-color: #0a84ff;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                }
                QPushButton#primaryButton:hover {
                    background-color: #409cff;
                }
                QPushButton#primaryButton:disabled {
                    background-color: #3a3a3c;
                    color: #636366;
                }
                QPushButton#secondaryButton {
                    background-color: #3a3a3c;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                }
                QPushButton#secondaryButton:hover {
                    background-color: #48484a;
                }
            """
        return """
            QPushButton#primaryButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton#primaryButton:hover {
                background-color: #0062cc;
            }
            QPushButton#primaryButton:disabled {
                background-color: #a0c4ff;
                color: #ffffff;
            }
            QPushButton#secondaryButton {
                background-color: #e8e8ed;
                color: #1d1d1f;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton#secondaryButton:hover {
                background-color: #dcdce0;
            }
        """

    @staticmethod
    def table_style(is_dark: bool = False) -> str:
        """表格样式"""
        if is_dark:
            return """
                QTableWidget {
                    background-color: #1c1c1e;
                    alternate-background-color: #2c2c2e;
                    border: 1px solid #38383a;
                    border-radius: 6px;
                    gridline-color: #38383a;
                }
                QTableWidget::item:selected {
                    background-color: #0a84ff;
                }
                QHeaderView::section {
                    background-color: #2c2c2e;
                    border-bottom: 2px solid #48484a;
                    padding: 6px 10px;
                    color: #ffffff;
                }
            """
        return """
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f9f9fb;
                border: 1px solid #e5e5ea;
                border-radius: 6px;
                gridline-color: #e5e5ea;
            }
            QTableWidget::item:selected {
                background-color: #007aff;
                color: white;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                border-bottom: 2px solid #d1d1d6;
                padding: 6px 10px;
            }
        """

    @staticmethod
    def workspace_style(is_dark: bool = False) -> str:
        """工作区样式"""
        if is_dark:
            return """
                #workspace {
                    background-color: #2c2c2e;
                    border-radius: 10px;
                    margin: 10px;
                }
            """
        return """
            #workspace {
                background-color: #ffffff;
                border-radius: 10px;
                margin: 10px;
            }
        """
