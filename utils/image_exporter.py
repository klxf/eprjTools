import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from PIL import Image
import base64
import io
from .database import DatabaseManager


class ImageExporter:
    def __init__(self, parent, directory):
        self.top = tk.Toplevel(parent)
        self.top.title("预览图批量导出工具")
        self.top.geometry("260x400")
        self.top.resizable(False, False)

        self.directory = directory
        self.setup_ui()
        self.load_projects()

    def setup_ui(self):
        self.frame = ttk.Frame(self.top, padding="10")
        self.frame.pack(fill=tk.BOTH, expand=True)

        # 列表框和滚动条
        listbox_frame = ttk.Frame(self.frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical")
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(listbox_frame,
                                  selectmode=tk.EXTENDED,
                                  yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)

        # 复选框
        self.sch_var = tk.BooleanVar()
        self.pcb_var = tk.BooleanVar()

        sch_checkbox = ttk.Checkbutton(self.frame,
                                       text="SCH",
                                       variable=self.sch_var)
        sch_checkbox.pack(side=tk.LEFT, padx=5, pady=5)

        pcb_checkbox = ttk.Checkbutton(self.frame,
                                       text="PCB",
                                       variable=self.pcb_var)
        pcb_checkbox.pack(side=tk.LEFT, padx=5, pady=5)

        # 导出按钮
        export_button = ttk.Button(self.frame,
                                   text="导出",
                                   command=self.export_selected)
        export_button.pack(side=tk.BOTTOM, pady=10)

    def load_projects(self):
        for file in os.listdir(self.directory):
            if file.endswith('.eprj'):
                self.listbox.insert(tk.END, file)

    def export_selected(self):
        selected_files = [self.listbox.get(i)
                          for i in self.listbox.curselection()]

        if not selected_files:
            messagebox.showwarning("警告", "请选择一个或多个工程进行导出")
            return

        export_directory = filedialog.askdirectory(title="请选择导出目录")
        if not export_directory:
            return

        missing_images = []
        progress_window = self.create_progress_window(len(selected_files))

        for index, file in enumerate(selected_files):
            self.export_project_images(file, export_directory, missing_images)
            progress_window.progress_bar["value"] = index + 1
            progress_window.update_idletasks()

        progress_window.destroy()
        self.show_export_result(missing_images)

    def export_project_images(self, file, export_directory, missing_images):
        db_path = os.path.join(self.directory, file)
        db_manager = DatabaseManager(db_path)
        name = file.replace('.eprj', '')

        if self.sch_var.get():
            self.export_document_type(db_manager, "SCH", 1,
                                      name, export_directory, missing_images)

        if self.pcb_var.get():
            self.export_document_type(db_manager, "PCB", 3,
                                      name, export_directory, missing_images)

    def export_document_type(self, db_manager, doc_type, type_id,
                             name, export_directory, missing_images):
        documents = db_manager.execute_query(
            "SELECT display_title, image FROM documents WHERE docType = ?",
            (type_id,)
        )

        for display_title, image_data in documents:
            if image_data:
                self.save_image(export_directory, doc_type,
                                name, display_title, image_data)
            else:
                missing_images.append((name, display_title, doc_type))

    def save_image(self, directory, doc_type, name, display_title, image_data):
        if image_data.startswith("data:image/webp;base64,"):
            image_data = image_data[len("data:image/webp;base64,"):]

        image = Image.open(io.BytesIO(base64.b64decode(image_data)))
        file_path = os.path.join(directory,
                                 f"[{doc_type}]{name}.{display_title}.png")
        image.save(file_path, "PNG")

    def create_progress_window(self, max_value):
        class ProgressWindow:
            def __init__(self, parent, maximum):
                self.window = tk.Toplevel(parent)
                self.window.title("导出进度")
                self.window.geometry("300x100")
                self.window.resizable(False, False)

                self.label = ttk.Label(self.window, text="正在导出...")
                self.label.pack(pady=10)

                self.progress_bar = ttk.Progressbar(
                    self.window,
                    orient="horizontal",
                    length=200,
                    mode="determinate",
                    maximum=maximum
                )
                self.progress_bar.pack(pady=10)

            def update_idletasks(self):
                self.window.update_idletasks()

            def destroy(self):
                self.window.destroy()

        return ProgressWindow(self.top, max_value)

    def show_export_result(self, missing_images):
        if missing_images:
            missing_images_str = "\n".join(
                [f"{file} - {display_title} ({doc_type})"
                 for file, display_title, doc_type in missing_images]
            )
            messagebox.showwarning(
                "警告",
                f"以下文档没有图片数据，请在嘉立创 EDA 保存一次后再试！\n{missing_images_str}")
