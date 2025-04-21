import tkinter as tk
from tkinter import ttk
from utils.image_exporter import ImageExporter

class ToolsWindow:
    def __init__(self, parent, directory):
        self.top = tk.Toplevel(parent)
        self.top.title("小工具")
        self.top.geometry("400x400")
        self.top.resizable(False, False)
        self.directory = directory
        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self.top, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        open_imagetool_button = ttk.Button(
            frame,
            text="预览图批量导出",
            command=self.open_imagetool,
            style='info.TButton'
        )
        open_imagetool_button.pack(side=tk.TOP, padx=5)

    def open_imagetool(self):
        ImageExporter(self.top, self.directory)
