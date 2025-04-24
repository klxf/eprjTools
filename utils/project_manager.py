import os
import json
from tkinter import messagebox, filedialog
from .database import DatabaseManager
from .config import load_config, save_config
from gui.preview_window import DocumentPreviewWindow


class ProjectManager:
    def __init__(self):
        self.config = load_config()
        self.directory = None
        self.current_db_path = None

    def set_directory(self, directory):
        """设置工作目录"""
        self.directory = directory

    def handle_listbox_click(self, event, treeview):
        if not self.directory:
            messagebox.showerror("错误", "工程目录未设置")
            return

        selected_file = event.widget.get(event.widget.curselection())
        self.current_db_path = os.path.join(self.directory, selected_file)
        self.display_tree_structure(selected_file, treeview)

    def handle_treeview_click(self, event, treeview):
        if not self.directory:
            messagebox.showerror("错误", "工程目录未设置")
            return

        selected_item = treeview.selection()[0]
        item_text = treeview.item(selected_item, "text")
        if " (UUID:" in item_text:
            title, uuid = item_text.split(" (UUID:")
            uuid = uuid.rstrip(")")
            self.display_document_preview(title.strip(), uuid)

    def display_tree_structure(self, file_name, treeview):
        for item in treeview.get_children():
            treeview.delete(item)

        db_path = os.path.join(self.directory, file_name)
        db_manager = DatabaseManager(db_path)

        try:
            project_data = db_manager.get_project_info()

            if project_data and project_data[0]:
                boards = json.loads(project_data[0][0])

                documents = db_manager.get_documents()
                documents_pcb_dict = {doc[0]: doc[1] for doc in documents if doc[2] == 3}
                documents_sch_dict = {doc[0]: doc[1] for doc in documents if doc[2] == 1}
                documents_other_dict = {doc[0]: doc[1] for doc in documents if doc[2] not in [1, 3]}

                # Get schematics
                schematics = db_manager.get_schematics()
                schematic_dict = {sch[0]: sch[1] for sch in schematics}
                schematic_sort_dict = {}
                for sch in schematics:
                    try:
                        schematic_sort_dict[sch[0]] = sch[2].split(',') if sch[2] else []
                    except Exception as e:
                        print(f"Error parsing sort data for schematic {sch[0]}: {e}")
                        schematic_sort_dict[sch[0]] = []

                displayed_uuids = set()

                for board in boards:
                    board_name = board['name']
                    sch_uuid = board.get('sch')
                    pcb_uuid = board.get('pcb')

                    board_item = treeview.insert("", "end", text=board_name)

                    if sch_uuid and (sch_title := schematic_dict.get(sch_uuid)):
                        sch_item = treeview.insert(board_item, "end",
                                                   text=f"[SCH] {sch_title} (UUID:{sch_uuid})")
                        displayed_uuids.add(sch_uuid)

                        for child_uuid in schematic_sort_dict.get(sch_uuid, []):
                            if child_title := documents_sch_dict.get(child_uuid):
                                treeview.insert(sch_item, "end",
                                                text=f"{child_title} (UUID:{child_uuid})")
                                displayed_uuids.add(child_uuid)

                    if pcb_uuid and (pcb_title := documents_pcb_dict.get(pcb_uuid)):
                        treeview.insert(board_item, "end",
                                        text=f"[PCB] {pcb_title} (UUID:{pcb_uuid})")
                        displayed_uuids.add(pcb_uuid)

                self._add_remaining_documents(treeview, documents_pcb_dict,
                                              documents_sch_dict, documents_other_dict,
                                              displayed_uuids)

        except Exception as e:
            messagebox.showerror("错误", f"加载工程结构时出错：{str(e)}")

    def _add_remaining_documents(self, treeview, pcb_dict, sch_dict,
                                 other_dict, displayed_uuids):
        """添加未在板件中显示的文档"""
        for uuid, title in pcb_dict.items():
            if uuid not in displayed_uuids:
                treeview.insert("", "end", text=f"[PCB] {title} (UUID:{uuid})")

        for uuid, title in sch_dict.items():
            if uuid not in displayed_uuids:
                treeview.insert("", "end", text=f"[SCH] {title} (UUID:{uuid})")

        for uuid, title in other_dict.items():
            if uuid not in displayed_uuids:
                treeview.insert("", "end", text=f"{title} (UUID:{uuid})")

    def display_document_preview(self, title, uuid):
        """显示文档预览"""
        if not self.directory or not hasattr(self, 'current_db_path'):
            messagebox.showerror("错误", "无法加载预览图")
            return

        try:
            db_manager = DatabaseManager(self.current_db_path)
            image_data = db_manager.execute_query(
                "SELECT image FROM documents WHERE uuid=? OR schematic_uuid=?",
                (uuid, uuid)
            )

            if not image_data or not image_data[0][0]:
                messagebox.showwarning("警告", "无法预览该文档，请在嘉立创EDA重新保存该文档")
                return

            # 创建预览窗口
            preview_window = DocumentPreviewWindow(None, title, uuid, image_data[0][0])

        except Exception as e:
            messagebox.showerror("错误", f"显示预览图时出错: {str(e)}")

    def open_project(self, listbox):
        selected_items = listbox.curselection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择一个工程进行打开")
            return

        if len(selected_items) > 1:
            messagebox.showwarning("警告", "只能选择一个工程进行打开")
            return

        selected_file = listbox.get(selected_items[0])
        try:
            os.startfile(os.path.join(self.directory, selected_file))
        except Exception as e:
            messagebox.showerror("错误", f"打开工程时出错: {str(e)}")
            return

    def delete_projects(self, listbox):
        if not self.directory:
            messagebox.showerror("错误", "工程目录未设置")
            return

        selected_items = listbox.curselection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择一个或多个工程进行删除")
            return

        for selected_item in selected_items:
            selected_file = listbox.get(selected_item)
            self.move_to_wastebasket(selected_file)

    def move_to_wastebasket(self, file_name):
        """移动文件到回收站"""
        from .wastebasket_manager import WastebasketManager
        wastebasket = WastebasketManager(self.directory)
        return wastebasket.move_to_wastebasket(file_name)

    def reselect_directory(self):
        """重新选择工程目录"""
        new_directory = filedialog.askdirectory(title="请选择工程目录")
        if new_directory:
            self.directory = new_directory
            self.config['project_directory'] = new_directory
            save_config(self.config)
            return new_directory
        return None
