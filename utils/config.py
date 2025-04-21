import os
import yaml
from tkinter import filedialog, messagebox


def get_project_directory():
    config_file = 'config.yaml'
    config = {}

    if not os.path.exists(config_file):
        project_directory = filedialog.askdirectory(title="请选择工程目录")
        if project_directory:
            config['project_directory'] = project_directory
            save_config(config)
    else:
        config = load_config()
        project_directory = config.get('project_directory')
        if not project_directory:
            messagebox.showerror("错误", "配置文件中未找到工程目录")

    if 'openeprj_cmd' not in config:
        setup_lceda_path(config)

    return project_directory


def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file) or {}


def save_config(config):
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file)


def setup_lceda_path(config):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,
                           r"LCEDA.Library.File\shell\open\commanda") as key:
            openeprj_cmd = winreg.QueryValue(key, None)
            config['openeprj_cmd'] = openeprj_cmd
            save_config(config)
    except FileNotFoundError:
        handle_missing_lceda(config)


def handle_missing_lceda(config):
    lceda_pro_path = filedialog.askopenfilename(
        title="请选择立创EDA（lceda-pro.exe）安装位置",
        filetypes=[("嘉立创EDA", "lceda-pro.exe")])
    if lceda_pro_path:
        config['openeprj_cmd'] = f'"{lceda_pro_path}" "%1"'
        save_config(config)
