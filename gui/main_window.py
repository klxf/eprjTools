import os
import tkinter as tk
from tkinter import ttk, messagebox
from .wastebasket_window import WastebasketWindow
from .details_window import DetailsWindow
from utils.project_manager import ProjectManager
from utils.file_operations import list_eprj_files
from tools.tools_window import ToolsWindow


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.setup_frames()
        self.setup_listbox()
        self.setup_treeview()
        self.setup_buttons()
        self.project_manager = ProjectManager()

    def setup_frames(self):
        self.frame = ttk.Frame(self.root, padding="10")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.frame, padding="10")
        self.right_frame = ttk.Frame(self.frame, padding="10")

        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure frame sizes
        self.left_frame.pack_propagate(False)
        self.left_frame.config(width=100)
        self.right_frame.pack_propagate(False)
        self.right_frame.config(width=300)

    def setup_listbox(self):
        scrollbar = ttk.Scrollbar(self.left_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.eprj_listbox = tk.Listbox(self.left_frame,
                                       yscrollcommand=scrollbar.set,
                                       selectmode=tk.EXTENDED)
        self.eprj_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.eprj_listbox.bind("<Double-1>", self.on_double_click_listbox)
        scrollbar.config(command=self.eprj_listbox.yview)

    def setup_treeview(self):
        right_bottom_frame = ttk.Frame(self.right_frame, padding="10")
        right_bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.eprj_treeview = ttk.Treeview(right_bottom_frame, show="tree")
        self.eprj_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.eprj_treeview.bind("<Double-1>", self.on_double_click_treeview)

        scrollbar = ttk.Scrollbar(right_bottom_frame,
                                  orient="vertical",
                                  command=self.eprj_treeview.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.eprj_treeview.configure(yscrollcommand=scrollbar.set)

    def setup_buttons(self):
        right_top_frame = ttk.Frame(self.right_frame, padding="10")
        right_top_frame.pack(side=tk.TOP, fill=tk.X)

        buttons = [
            ("删除", self.on_delete_click, 'danger'),
            ("打开", self.on_open_click, 'success'),
            ("详细", self.on_details_click, 'success'),
            ("回收站", self.on_open_wastebasket_click, 'info'),
            ("选择目录", self.reselect_project_directory, 'info'),
            ("小工具", self.open_tools_window, 'info')
        ]

        for text, command, style in buttons:
            btn = ttk.Button(right_top_frame,
                             text=text,
                             command=command,
                             style=f'{style}.TButton')
            btn.pack(side=tk.LEFT, padx=5)

    def initialize(self, directory):
        self.directory = directory
        self.project_manager.set_directory(directory)
        self.refresh_listbox()
        self.root.title(f"嘉立创EDA工程管理工具 - {directory}")

    def refresh_listbox(self):
        eprj_files = list_eprj_files(self.directory)
        self.eprj_listbox.delete(0, tk.END)
        for file in eprj_files:
            self.eprj_listbox.insert(tk.END, file)

    # Event handlers
    def on_double_click_listbox(self, event):
        self.project_manager.handle_listbox_click(event, self.eprj_treeview)

    def on_double_click_treeview(self, event):
        self.project_manager.handle_treeview_click(event, self.eprj_treeview)

    def on_delete_click(self):
        self.project_manager.delete_projects(self.eprj_listbox)
        self.refresh_listbox()

    def on_open_click(self):
        self.project_manager.open_project(self.eprj_listbox)

    def on_details_click(self):
        selected_items = self.eprj_listbox.curselection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择一个工程查看详细信息")
            return

        selected_file = self.eprj_listbox.get(selected_items[0])
        db_path = os.path.join(self.directory, selected_file)
        details_window = DetailsWindow(self.root)
        details_window.load_project_details(db_path)

    def on_open_wastebasket_click(self):
        WastebasketWindow(self.root, self.directory, self)

    def reselect_project_directory(self):
        new_directory = self.project_manager.reselect_directory()
        if new_directory:
            self.directory = new_directory
            self.refresh_listbox()
            self.root.title(f"嘉立创EDA工程管理工具 - {new_directory}")

    def open_tools_window(self):
        ToolsWindow(self.root, self.directory)
