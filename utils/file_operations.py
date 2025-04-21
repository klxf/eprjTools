import os
import shutil
from tkinter import messagebox


def list_eprj_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.eprj')]


def move_file(src, dst):
    try:
        shutil.move(src, dst)
        return True
    except Exception as e:
        messagebox.showerror("错误", f"移动文件时出错: {e}")
        return False


def delete_file(path):
    try:
        os.remove(path)
        return True
    except Exception as e:
        messagebox.showerror("错误", f"删除文件时出错: {e}")
        return False
