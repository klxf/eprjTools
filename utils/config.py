import os
import yaml
from tkinter import filedialog, messagebox


def get_project_directory():
    config = load_config()

    if 'project_directory' not in config:
        messagebox.showerror("错误", "配置文件中未找到工程目录")
        handle_missing_project_directory(config)

    project_directory = config['project_directory']

    return project_directory


def load_config():
    if not os.path.exists('config.yaml'):
        with open('config.yaml', 'w') as file:
            yaml.dump({}, file)

    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file) or {}


def save_config(config):
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file)


def handle_missing_project_directory(config):
    project_directory = filedialog.askdirectory(title="请选择工程目录")
    if project_directory:
        config['project_directory'] = project_directory
        save_config(config)
    else:
        messagebox.showerror("错误", "未选择工程目录")
