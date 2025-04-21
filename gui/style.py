import tkinter as tk
from ttkbootstrap import Style
import os


def setup_style():
    root = tk.Tk()
    root.title("嘉立创EDA工程管理工具")
    root.geometry("800x400")
    root.resizable(False, False)
    root.iconbitmap(os.path.join(os.path.dirname(__file__), '..', 'icon.ico'))
    Style(theme='flatly').theme_use()
    return root
