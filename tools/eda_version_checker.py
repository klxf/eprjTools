import shutil
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import threading
import tempfile
import os
from tkinter import filedialog
import platform
import subprocess
from .base import BaseTool


class VersionCheckerTool(BaseTool):
    @property
    def name(self):
        return "EDA版本检索"

    @property
    def description(self):
        return "检查和下载嘉立创EDA专业版的各个版本"

    def create_window(self):
        self.window = VersionCheckerWindow(self.parent)

    def show(self):
        if not self.window:
            self.create_window()


class VersionCheckerWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("EDA版本检索")
        self.top.iconbitmap(os.path.join(os.path.dirname(__file__), '..', 'icon.ico'))
        window_width = 800
        window_height = 600
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.top.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.top.minsize(600, 400)  # 设置最小窗口大小

        self.existing_versions = []
        self.setup_ui()

    def setup_ui(self):
        # 创建主框架并添加内边距
        main_frame = ttk.Frame(self.top, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建左侧和右侧框架
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 左侧区域: 版本设置和检查按钮
        settings_frame = ttk.LabelFrame(left_frame, text="版本范围设置 - 2.2.A.B", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # 创建网格布局
        for i in range(4):
            settings_frame.grid_columnconfigure(1, weight=1)

        # 版本范围输入框
        labels = ["第三段起始值:", "第三段结束值:",
                  "第四段起始值:", "第四段结束值:"]
        entries = []
        default_values = ["40", "42", "0", "9"]

        for i, (label, default) in enumerate(zip(labels, default_values)):
            ttk.Label(settings_frame, text=label).grid(row=i, column=0,
                                                       sticky=tk.W, padx=(0, 5), pady=5)
            entry = ttk.Entry(settings_frame)
            entry.insert(0, default)
            entry.grid(row=i, column=1, sticky=tk.EW, pady=5)
            entries.append(entry)

        self.a_start_entry, self.a_end_entry, \
            self.b_start_entry, self.b_end_entry = entries

        # 按钮区域
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.check_button = ttk.Button(button_frame, text="检查版本",
                                       command=self.start_check)
        self.check_button.pack(side=tk.LEFT, expand=True, padx=5)

        # 自动打开选项
        self.auto_open_var = tk.BooleanVar()
        auto_open_check = ttk.Checkbutton(button_frame, text="下载完成后自动打开",
                                          variable=self.auto_open_var)
        auto_open_check.pack(side=tk.LEFT, expand=True, padx=5)

        # 版本检查进度条
        self.check_progress_bar = ttk.Progressbar(left_frame,
                                                  mode='determinate')

        # 下载进度条
        self.download_progress_bar = ttk.Progressbar(left_frame,
                                                     mode='determinate')

        # 输出日志区域
        log_frame = ttk.LabelFrame(left_frame, text="日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.output_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,
                                                     height=8)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # 右侧区域: 版本列表
        versions_frame = ttk.LabelFrame(right_frame, text="可用版本", padding="5")
        versions_frame.pack(fill=tk.BOTH, expand=True)

        # 创建带滚动条的列表框
        listbox_frame = ttk.Frame(versions_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.existing_versions_listbox = tk.Listbox(listbox_frame,
                                                    yscrollcommand=scrollbar.set,
                                                    selectmode=tk.SINGLE,
                                                    font=("Microsoft YaHei UI", 10)
                                                    )
        self.existing_versions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.existing_versions_listbox.yview)

        # 绑定双击事件
        self.existing_versions_listbox.bind("<Double-Button-1>", self.download_version)

        # 添加提示标签
        ttk.Label(versions_frame,
                  text="双击版本号下载安装包",
                  foreground="gray").pack(pady=5)

    def check_versions_thread(self, base_url, a_start, a_end, b_start, b_end):
        """检查版本的线程函数"""
        self.output_text.delete(1.0, tk.END)
        self.existing_versions.clear()
        self.existing_versions_listbox.delete(0, tk.END)

        total_checks = (a_end - a_start + 1) * (b_end - b_start + 1)
        checked_count = 0
        self.check_progress_bar['maximum'] = total_checks
        self.check_progress_bar['value'] = 0
        self.check_progress_bar.pack(fill=tk.X, pady=10)

        try:
            for a in range(a_start, a_end + 1):
                for b in range(b_start, b_end + 1):
                    version = f"2.2.{a}.{b}"
                    url = base_url.replace("${version}", version)
                    try:
                        response = requests.get(url, stream=True)
                        if response.status_code == 200:
                            self.existing_versions.append(version)
                            self.existing_versions_listbox.insert(tk.END, version)
                            self.output_text.insert(tk.END,
                                                    f"版本 {version} 存在\n")
                        response.close()
                    except requests.exceptions.RequestException as e:
                        self.output_text.insert(tk.END, f"请求 {url} 失败: {e}\n")
                    finally:
                        checked_count += 1
                        self.check_progress_bar['value'] = checked_count
                        self.output_text.see(tk.END)
                        self.top.update_idletasks()

            if self.existing_versions:
                self.output_text.insert(tk.END,
                                        f"\n检查完成，找到 {len(self.existing_versions)} 个可用版本。\n")
            else:
                self.output_text.insert(tk.END,
                                        "\n检查完成，未找到任何可用版本。\n")

        except Exception as e:
            self.output_text.insert(tk.END, f"\n检查过程出错: {str(e)}\n")
        finally:
            self.output_text.see(tk.END)
            self.check_progress_bar.pack_forget()
            self.check_button.config(state=tk.NORMAL, text="检查版本")

    def start_check(self):
        """开始检查版本"""
        try:
            a_start = int(self.a_start_entry.get())
            a_end = int(self.a_end_entry.get())
            b_start = int(self.b_start_entry.get())
            b_end = int(self.b_end_entry.get())

            if a_start > a_end or b_start > b_end:
                messagebox.showerror("错误", "起始值不能大于结束值")
                return

            if (a_end - a_start + 1) * (b_end - b_start + 1) > 100:
                if not messagebox.askyesno("确认",
                                           "检查范围过大可能需要较长时间，是否继续？"):
                    return

            base_url = "https://image.lceda.cn/files/lceda-pro-windows-x64-${version}.exe"
            self.check_button.config(state=tk.DISABLED, text="正在检查...")

            thread = threading.Thread(
                target=self.check_versions_thread,
                args=(base_url, a_start, a_end, b_start, b_end)
            )
            thread.daemon = True
            thread.start()

        except ValueError:
            messagebox.showerror("错误", "请输入有效的整数范围")
            self.check_button.config(state=tk.NORMAL, text="检查版本")

    def download_file(self, url, save_path, version):
        """在单独的线程中下载文件，使用分块下载并保存在临时文件夹"""
        temp_file = None
        try:
            self.output_text.insert(tk.END, f"开始下载版本 {version}...\n")
            self.output_text.see(tk.END)

            # 创建临时文件
            temp_fd, temp_path = tempfile.mkstemp(suffix='.tmp', prefix='lceda_')
            os.close(temp_fd)
            temp_file = temp_path

            # 获取文件大小
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))

            if total_size == 0:
                raise Exception("无法获取文件大小")

            # 设置分块大小和数量
            chunk_size = 1024 * 1024 * 5  # 5MB 每块
            num_chunks = total_size // chunk_size + (1 if total_size % chunk_size else 0)

            # 初始化进度条
            self.download_progress_bar['maximum'] = total_size
            self.download_progress_bar['value'] = 0
            self.download_progress_bar.pack(fill=tk.X, pady=10)

            downloaded = 0
            chunks = []

            # 创建临时文件列表用于存储分块
            temp_chunks = []
            for chunk_num in range(num_chunks):
                chunk_fd, chunk_path = tempfile.mkstemp(suffix=f'.chunk{chunk_num}', prefix='lceda_')
                os.close(chunk_fd)
                temp_chunks.append(chunk_path)
                chunks.append({'start': chunk_num * chunk_size,
                               'end': min((chunk_num + 1) * chunk_size - 1, total_size - 1),
                               'path': chunk_path})

            # 下载每个分块
            for i, chunk in enumerate(chunks):
                if not self._running:
                    raise Exception("下载已取消")

                headers = {'Range': f'bytes={chunk["start"]}-{chunk["end"]}'}
                response = requests.get(url, headers=headers, stream=True)
                response.raise_for_status()

                with open(chunk['path'], 'wb') as f:
                    for data in response.iter_content(1024 * 1024):  # 1MB 读取缓冲
                        if not self._running:
                            raise Exception("下载已取消")
                        f.write(data)
                        downloaded += len(data)
                        self.download_progress_bar['value'] = downloaded

                        # 显示下载进度百分比
                        percent = (downloaded / total_size) * 100
                        self.output_text.delete("end-2c linestart", "end-1c lineend")
                        self.output_text.insert(tk.END,
                                                f"正在下载版本 {version}... {percent:.1f}%\n")
                        self.output_text.see(tk.END)
                        self.top.update_idletasks()

            # 合并所有分块到临时文件
            with open(temp_file, 'wb') as outfile:
                for chunk in chunks:
                    if not self._running:
                        raise Exception("下载已取消")
                    with open(chunk['path'], 'rb') as infile:
                        shutil.copyfileobj(infile, outfile)

            # 验证文件大小
            actual_size = os.path.getsize(temp_file)
            if actual_size != total_size:
                raise Exception(f"文件大小不匹配 (预期: {total_size}, 实际: {actual_size})")

            # 移动临时文件到最终位置
            shutil.move(temp_file, save_path)
            temp_file = None  # 防止finally中删除已移动的文件

            self.output_text.insert(tk.END,
                                    f"版本 {version} 下载完成，保存到: {save_path}\n")
            self.output_text.see(tk.END)

            # 如果选择了自动打开选项
            if self.auto_open_var.get():
                system = platform.system()
                if system == "Windows":
                    os.startfile(save_path)
                elif system == "Darwin":  # macOS
                    subprocess.run(['open', save_path])
                elif system == "Linux":
                    subprocess.run(['xdg-open', save_path])
                else:
                    messagebox.showinfo("提示",
                                        f"下载完成，文件已保存到：{save_path}，请手动打开。")

        except Exception as e:
            if str(e) == "下载已取消":
                self.output_text.insert(tk.END, f"版本 {version} 下载已取消\n")
            else:
                self.output_text.insert(tk.END, f"下载版本 {version} 失败: {e}\n")
            # 如果下载失败，删除未完成的文件
            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except:
                    pass

        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

            # 清理分块临时文件
            if 'temp_chunks' in locals():
                for chunk_path in temp_chunks:
                    try:
                        if os.path.exists(chunk_path):
                            os.remove(chunk_path)
                    except:
                        pass

            self.download_progress_bar.pack_forget()
            self._running = False
            self.output_text.see(tk.END)
            if 'response' in locals():
                response.close()

    def download_version(self, event):
        """处理版本下载"""
        if hasattr(self, '_running') and self._running:
            messagebox.showwarning("警告", "已有下载任务正在进行中")
            return

        selected_index = self.existing_versions_listbox.curselection()
        if not selected_index:
            return

        version = self.existing_versions[selected_index[0]]
        base_url = "https://image.lceda.cn/files/lceda-pro-windows-x64-${version}.exe"
        download_url = base_url.replace("${version}", version)
        filename = f"lceda-pro-windows-x64-{version}.exe"

        save_path = filedialog.asksaveasfilename(
            defaultextension=".exe",
            initialfile=filename,
            title=f"保存 {filename} 到...",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )

        if save_path:
            self._running = True
            download_thread = threading.Thread(
                target=self.download_file,
                args=(download_url, save_path, version)
            )
            download_thread.daemon = True
            download_thread.start()
