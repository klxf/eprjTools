from abc import ABC, abstractmethod
import tkinter as tk


class BaseTool(ABC):
    """工具基类，所有工具都应该继承这个类"""

    def __init__(self, parent, directory):
        self.parent = parent
        self.directory = directory
        self.window = None

    @abstractmethod
    def create_window(self):
        """创建工具窗口"""
        pass

    @abstractmethod
    def show(self):
        """显示工具窗口"""
        pass

    @property
    @abstractmethod
    def name(self):
        """工具名称"""
        return ""

    @property
    @abstractmethod
    def description(self):
        """工具描述"""
        return ""
