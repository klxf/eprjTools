import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from PIL import Image
import base64
import io
from utils.database import DatabaseManager
from .base import BaseTool


class ImageExporterTool(BaseTool):
    @property
    def name(self):
        return "预览图批量导出"

    @property
    def description(self):
        return "批量导出工程中的原理图和PCB预览图"

    def create_window(self):
        self.window = ImageExporterWindow(self.parent, self.directory)

    def show(self):
        if not self.window:
            self.create_window()


class ImageExporterWindow:
    def __init__(self, parent, directory):
        self.top = tk.Toplevel(parent)
        self.top.title("预览图批量导出工具")
        self.top.geometry("260x400")
        self.top.resizable(False, False)

        self.directory = directory
        self.exporter = ImageExporter(directory)
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

        self.listbox = tk.Listbox(
            listbox_frame,
            selectmode=tk.EXTENDED,
            yscrollcommand=self.scrollbar.set
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)

        # 复选框
        checkbox_frame = ttk.Frame(self.frame)
        checkbox_frame.pack(fill=tk.X)

        self.sch_var = tk.BooleanVar()
        self.pcb_var = tk.BooleanVar()

        ttk.Checkbutton(
            checkbox_frame,
            text="SCH",
            variable=self.sch_var
        ).pack(side=tk.LEFT, padx=5)

        ttk.Checkbutton(
            checkbox_frame,
            text="PCB",
            variable=self.pcb_var
        ).pack(side=tk.LEFT, padx=5)

        # 导出按钮
        ttk.Button(
            self.frame,
            text="导出",
            command=self.export_selected
        ).pack(side=tk.BOTTOM, pady=10)

    def load_projects(self):
        for project in self.exporter.list_projects():
            self.listbox.insert(tk.END, project)

    def export_selected(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "请选择一个或多个工程进行导出")
            return

        selected_files = [self.listbox.get(i) for i in selected_indices]
        export_types = []
        if self.sch_var.get():
            export_types.append("SCH")
        if self.pcb_var.get():
            export_types.append("PCB")

        if not export_types:
            messagebox.showwarning("警告", "请选择需要导出的文档类型（SCH 或 PCB）")
            return

        self.exporter.export_files(selected_files, export_types)


class ImageExporter:
    def __init__(self, directory):
        self.directory = directory
        self._running = False

    def list_projects(self):
        """列出所有工程文件"""
        return [f for f in os.listdir(self.directory)
                if f.endswith('.eprj')]

    def export_files(self, files, export_types):
        """导出选中的文件"""
        if not files:
            messagebox.showwarning("警告", "请选择一个或多个工程进行导出")
            return

        if self._running:
            messagebox.showwarning("警告", "导出任务正在进行中")
            return

        export_directory = filedialog.askdirectory(title="请选择导出目录")
        if not export_directory:
            return

        # 创建进度窗口
        progress_window = self._create_progress_window(len(files))

        # 启动导出线程
        self._running = True
        export_thread = threading.Thread(
            target=self._export_thread,
            args=(files, export_types, export_directory, progress_window)
        )
        export_thread.start()

        # 启动检查线程状态的定时器
        self._check_thread_status(export_thread, progress_window)

    def _export_thread(self, files, export_types, export_directory, progress_window):
        """在单独的线程中执行导出操作"""
        try:
            missing_images = []
            for i, file in enumerate(files, 1):
                if not self._running:
                    break

                self._export_project(
                    file,
                    export_directory,
                    export_types,
                    missing_images
                )
                progress_window.window.after(
                    0,
                    progress_window.update_progress,
                    i,
                    len(files)
                )

            if missing_images and self._running:
                progress_window.window.after(
                    0,
                    self._show_missing_warning,
                    missing_images
                )

        except Exception as e:
            progress_window.window.after(
                0,
                lambda: messagebox.showerror("错误", f"导出过程中出错：{str(e)}")
            )
        finally:
            self._running = False

    def _check_thread_status(self, thread, progress_window):
        """检查导出线程的状态"""
        if thread.is_alive():
            progress_window.window.after(100,
                                         self._check_thread_status,
                                         thread,
                                         progress_window)
        else:
            progress_window.destroy()

    def _create_progress_window(self, total):
        """创建进度窗口"""

        class ProgressWindow:
            def __init__(self, total):
                self.window = tk.Toplevel()
                self.window.title("导出进度")
                self.window.geometry("300x150")
                self.window.resizable(False, False)

                self.window.update_idletasks()
                width = self.window.winfo_width()
                height = self.window.winfo_height()
                x = (self.window.winfo_screenwidth() // 2) - (width // 2)
                y = (self.window.winfo_screenheight() // 2) - (height // 2)
                self.window.geometry(f'+{x}+{y}')

                self.label = ttk.Label(self.window, text="正在导出...")
                self.label.pack(pady=10)

                self.progress_bar = ttk.Progressbar(
                    self.window,
                    orient="horizontal",
                    length=200,
                    mode="determinate",
                    maximum=total
                )
                self.progress_bar.pack(pady=10)

                self.progress_text = ttk.Label(self.window, text="0%")
                self.progress_text.pack(pady=5)

                self.cancel_button = ttk.Button(
                    self.window,
                    text="取消",
                    command=self.cancel
                )
                self.cancel_button.pack(pady=5)

                self.window.protocol("WM_DELETE_WINDOW", lambda: None)

            def update_progress(self, current, total):
                self.progress_bar["value"] = current
                percentage = int((current / total) * 100)
                self.progress_text["text"] = f"{percentage}% ({current}/{total})"
                self.window.update_idletasks()

            def cancel(self):
                if messagebox.askyesno("确认", "确定要取消导出吗？"):
                    nonlocal self_ref
                    self_ref._running = False

            def destroy(self):
                self.window.destroy()

        self_ref = self
        return ProgressWindow(total)

    def _export_project(self, file, export_dir, types, missing):
        """导出单个工程的预览图"""
        if not self._running:
            return

        try:
            db_path = os.path.join(self.directory, file)
            db = DatabaseManager(db_path)
            name = file.replace('.eprj', '')

            for doc_type in types:
                if not self._running:
                    return

                type_id = 1 if doc_type == "SCH" else 3
                documents = db.execute_query("""
                    SELECT display_title, image 
                    FROM documents 
                    WHERE docType = ?
                """, (type_id,))

                for title, image_data in documents:
                    if not self._running:
                        return

                    if image_data:
                        self._save_image(export_dir, doc_type, name, title, image_data)
                    else:
                        missing.append((file, title, doc_type))
        except Exception as e:
            missing.append((file, "错误", str(e)))

    def _save_image(self, directory, doc_type, name, title, image_data):
        """保存图片文件"""
        if not self._running:
            return

        try:
            if image_data.startswith("data:image/webp;base64,"):
                image_data = image_data[len("data:image/webp;base64,"):]

            image = Image.open(io.BytesIO(base64.b64decode(image_data)))
            file_path = os.path.join(directory,
                                     f"[{doc_type}]{name}.{title}.png")
            image.save(file_path, "PNG")
        except Exception as e:
            raise Exception(f"保存图片 [{doc_type}]{name}.{title}.png 时出错：{str(e)}")

    def _show_missing_warning(self, missing_images):
        """显示缺失图片的警告"""
        missing_str = "\n".join(
            [f"{f} - {t} ({d})" for f, t, d in missing_images]
        )
        messagebox.showwarning(
            "警告",
            f"以下文档没有图片数据或处理过程中出错，请检查！\n{missing_str}"
        )
