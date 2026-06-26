# -*- coding: utf-8 -*-
"""
工具窗口管理器 - 单例管理所有独立工具窗口
确保每个工具窗口唯一实例，状态保持
"""
import weakref
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QDialog


class ToolManager(QObject):
    """工具窗口管理器 - 单例模式"""

    _instance = None
    _instances = {}
    _classes = {}

    tool_opened = pyqtSignal(str)
    tool_closed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = ToolManager()
        return cls._instance

    @classmethod
    def register_tool(cls, tool_name: str, tool_class):
        """注册工具类"""
        cls._classes[tool_name] = tool_class

    @classmethod
    def show_tool(cls, tool_name: str, tool_class=None, parent=None,
                  *args, **kwargs):
        """显示工具窗口（单例）"""
        inst = cls.instance()
        return inst._show_tool_impl(tool_name, tool_class, parent, *args, **kwargs)

    def _show_tool_impl(self, tool_name: str, tool_class, parent, *args, **kwargs):
        if tool_class is not None:
            self._classes[tool_name] = tool_class

        widget = self._instances.get(tool_name)
        if widget is None or not isinstance(widget, QWidget):
            actual_class = tool_class if tool_class else self._classes.get(tool_name)
            if actual_class is None:
                return None
            widget = actual_class(parent, *args, **kwargs)

            if isinstance(widget, QDialog):
                widget.setModal(False)
                widget.setWindowFlags(widget.windowFlags() | Qt.Window)
            elif isinstance(widget, QWidget) and widget.isWindow() is False:
                widget.setWindowFlags(widget.windowFlags() | Qt.Window)

            self._instances[tool_name] = widget

            mgr_ref = weakref.ref(self)
            def _on_destroyed(name=tool_name):
                mgr = mgr_ref()
                if mgr is None:
                    return
                try:
                    if name in mgr._instances:
                        del mgr._instances[name]
                    mgr.tool_closed.emit(name)
                except RuntimeError:
                    pass

            widget.destroyed.connect(_on_destroyed)
            self.tool_opened.emit(tool_name)

        widget.show()
        widget.raise_()
        widget.activateWindow()
        return widget

    @classmethod
    def close_tool(cls, tool_name: str):
        """关闭工具窗口"""
        inst = cls._instances.get(tool_name)
        if inst:
            try:
                inst.close()
            except Exception:
                pass

    @classmethod
    def close_all(cls):
        """关闭所有工具窗口"""
        names = list(cls._instances.keys())
        for name in names:
            cls.close_tool(name)

    @classmethod
    def is_open(cls, tool_name: str) -> bool:
        """工具是否已打开"""
        inst = cls._instances.get(tool_name)
        return inst is not None and isinstance(inst, QWidget) and inst.isVisible()

    @classmethod
    def get_tool(cls, tool_name: str):
        """获取工具窗口实例"""
        return cls._instances.get(tool_name)

    @classmethod
    def list_open_tools(cls) -> list:
        """列出所有已打开的工具名"""
        return [name for name, inst in cls._instances.items()
                if inst is not None and isinstance(inst, QWidget)]
