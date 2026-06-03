"""模块基类 — 定义所有功能模块的统一接口"""
from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget


class BaseModule(ABC):
    """所有功能模块的基类

    每个功能模块（PDF合并、PDF编辑、表格合并、表头匹配...）
    都继承此类并实现相应方法。

    属性:
        name: 模块显示名称
        icon: 图标名称/路径
        category: 分类，用于导航分组
    """

    name: str = ""
    icon: str = ""
    category: str = ""

    def __init__(self):
        self._widget: QWidget | None = None

    @abstractmethod
    def create_workspace(self) -> QWidget:
        """创建模块的工作区 UI

        返回一个 QWidget，作为该模块在右侧工作区的内容。
        只在模块首次激活时调用一次。
        """
        ...

    @property
    def workspace(self) -> QWidget | None:
        """获取已创建的工作区 Widget"""
        return self._widget

    @workspace.setter
    def workspace(self, widget: QWidget):
        self._widget = widget

    def on_enter(self):
        """模块被激活时调用（切换到该模块时）"""
        pass

    def on_leave(self):
        """模块被停用时调用（切换到其他模块时）"""
        pass

    def on_file_dropped(self, file_paths: list[str]):
        """文件拖拽到工作区时调用

        Args:
            file_paths: 拖入的文件路径列表
        """
        pass
