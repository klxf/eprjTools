import tkinter as tk
from tkinter import ttk
from utils.file_operations import list_eprj_files
from utils.wastebasket_manager import WastebasketManager

class WastebasketWindow:
    def __init__(self, parent, directory, main_window):
        self.top = tk.Toplevel(parent)
        self.top.title("回收站")
        self.top.geometry("260x400")
        self.top.resizable(False, False)
        
        self.directory = directory
        self.main_window = main_window
        self.wastebasket_manager = WastebasketManager(directory)
        
        self.setup_ui()
        self.load_files()

    def setup_ui(self):
        self.frame = ttk.Frame(self.top, padding="10")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(self.frame)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.frame, orient="vertical",
                                command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self.top, padding="10")
        button_frame.pack(fill=tk.X)

        restore_button = ttk.Button(button_frame, text="还原",
                                  command=self.restore_file,
                                  style='success.TButton')
        restore_button.pack(side=tk.LEFT, padx=5)

        delete_button = ttk.Button(button_frame, text="删除",
                                 command=self.delete_file,
                                 style='danger.TButton')
        delete_button.pack(side=tk.LEFT, padx=5)

    def load_files(self):
        files = self.wastebasket_manager.list_files()
        for file in files:
            self.listbox.insert(tk.END, file)

    def restore_file(self):
        if selected := self.listbox.curselection():
            file_name = self.listbox.get(selected)
            if self.wastebasket_manager.restore_file(file_name):
                self.listbox.delete(selected)
                self.main_window.refresh_listbox()

    def delete_file(self):
        if selected := self.listbox.curselection():
            file_name = self.listbox.get(selected)
            if self.wastebasket_manager.delete_file(file_name):
                self.listbox.delete(selected)
