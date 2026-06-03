"""事件总线 — 模块间松耦合通信"""
from typing import Callable
from collections import defaultdict


class EventBus:
    """全局事件总线，用于模块间发送消息"""

    def __init__(self):
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable):
        """订阅事件

        Args:
            event: 事件名称，如 "pdf.merged", "table.matched"
            callback: 回调函数
        """
        if callback not in self._listeners[event]:
            self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable):
        """取消订阅"""
        if callback in self._listeners[event]:
            self._listeners[event].remove(callback)

    def emit(self, event: str, **data):
        """发送事件

        Args:
            event: 事件名称
            **data: 随事件传递的数据
        """
        for callback in self._listeners[event]:
            try:
                callback(data)
            except Exception as e:
                print(f"[EventBus] 事件 {event} 回调异常: {e}")

    def clear(self):
        """清除所有监听器"""
        self._listeners.clear()


# 全局单例
bus = EventBus()


# 预定义事件常量
class Events:
    # PDF 事件
    PDF_FILES_LOADED = "pdf.files_loaded"
    PDF_MERGE_START = "pdf.merge_start"
    PDF_MERGE_COMPLETE = "pdf.merge_complete"
    PDF_EDIT_COMPLETE = "pdf.edit_complete"
    PDF_PAGE_SELECTED = "pdf.page_selected"

    # 表格事件
    TABLE_FILES_LOADED = "table.files_loaded"
    TABLE_MERGE_START = "table.merge_start"
    TABLE_MERGE_COMPLETE = "table.merge_complete"
    TABLE_MATCH_START = "table.match_start"
    TABLE_MATCH_COMPLETE = "table.match_complete"

    # 应用事件
    STATUS_MESSAGE = "app.status_message"
    PROGRESS_UPDATE = "app.progress_update"
    THEME_CHANGED = "app.theme_changed"
