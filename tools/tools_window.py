import os
import tkinter as tk
from tkinter import ttk
from .image_exporter import ImageExporterTool
from .eda_version_checker import VersionCheckerTool


class ToolsWindow:
    def __init__(self, parent, directory):
        self.top = tk.Toplevel(parent)
        self.top.title("小工具")
        self.top.geometry("400x400")
        self.top.resizable(False, False)

        self.directory = directory
        self.tools = self._register_tools()
        self.top.iconbitmap(os.path.join(os.path.dirname(__file__), '..', 'icon.ico'))
        self.setup_ui()

    def _register_tools(self):
        """注册所有可用的工具"""
        return [
            ImageExporterTool,
            VersionCheckerTool,
        ]

    def setup_ui(self):
        frame = ttk.Frame(self.top, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # 创建工具列表
        for tool_class in self.tools:
            tool = tool_class(self.top, self.directory)
            btn = ttk.Button(
                frame,
                text=tool.name,
                command=lambda t=tool: t.show(),
                style='info.TButton'
            )
            btn.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)
