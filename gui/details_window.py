import tkinter as tk
from tkinter import ttk
from utils.database import DatabaseManager


class DetailsWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("工程详细信息")
        self.top.geometry("300x400")
        self.top.resizable(False, False)

        self.setup_ui()
        self.bind_events()

    def setup_ui(self):
        frame = ttk.Frame(self.top, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # 创建TreeView用于显示详细信息
        columns = ("key", "value")
        self.treeview = ttk.Treeview(frame, columns=columns,
                                     show="headings",
                                     selectmode="extended")
        self.treeview.pack(fill=tk.BOTH, expand=True)

        # 设置列标题和宽度
        self.treeview.heading("key", text="项目")
        self.treeview.heading("value", text="值")
        self.treeview.column("key", width=50)
        self.treeview.column("value", width=100)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(frame, orient="vertical",
                                  command=self.treeview.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.treeview.configure(yscrollcommand=scrollbar.set)

    def bind_events(self):
        # 绑定复制功能到Ctrl+C
        self.top.bind_all("<Control-c>", self.copy_to_clipboard)

    def copy_to_clipboard(self, event):
        selected_items = self.treeview.selection()
        if not selected_items:
            return

        clipboard_text = ""
        for item in selected_items:
            item_values = self.treeview.item(item, "values")
            clipboard_text += f"{item_values[0]}: {item_values[1]}\n"

        self.top.clipboard_clear()
        self.top.clipboard_append(clipboard_text.strip())
        self.top.update()

    def load_project_details(self, db_path):
        """加载并显示项目详细信息"""
        self.clear_details()
        db_manager = DatabaseManager(db_path)

        try:
            # 获取项目基本信息
            project_info = db_manager.execute_query("""
                SELECT uuid, name, owner_uuid, creator_uuid, 
                       modifier_uuid, updated_at, created_at 
                FROM projects
            """)

            if project_info and project_info[0]:
                project = project_info[0]
                self._add_detail_item("UUID", project[0])
                self._add_detail_item("名称", project[1])
                self._add_detail_item("所有者", project[2])
                self._add_detail_item("创建者", project[3])
                self._add_detail_item("修改者", project[4])
                self._add_detail_item("更新于", project[5])
                self._add_detail_item("创建于", project[6])

            # 获取器件和资源数量
            device_count = db_manager.execute_query("SELECT COUNT(*) FROM devices")
            if device_count:
                self._add_detail_item("包含器件数", device_count[0][0])

            resource_count = db_manager.execute_query("SELECT COUNT(*) FROM resources")
            if resource_count:
                self._add_detail_item("包含资源数", resource_count[0][0])

        except Exception as e:
            self._add_detail_item("错误", f"加载项目信息时出错: {str(e)}")

    def _add_detail_item(self, key, value):
        self.treeview.insert("", tk.END, values=(key, value))

    def clear_details(self):
        for item in self.treeview.get_children():
            self.treeview.delete(item)
