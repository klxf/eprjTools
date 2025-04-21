import tkinter as tk
from ttkbootstrap import Style
import os


def setup_style():
    root = tk.Tk()
    root.title("嘉立创EDA工程管理工具")
    window_width = 800
    window_height = 400
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.resizable(False, False)
    root.iconbitmap(os.path.join(os.path.dirname(__file__), '..', 'icon.ico'))
    Style(theme='flatly').theme_use()
    return root
