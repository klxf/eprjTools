import os
import sqlite3
import json
from ttkbootstrap import Style
import tkinter as tk
from tkinter import ttk
from tkinter import Toplevel, messagebox, Canvas, filedialog
from PIL import Image, ImageTk
import base64
import io
import shutil
import yaml
import winreg

icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')


def get_project_directory():
    config_file = 'config.yaml'
    config = {}

    if not os.path.exists(config_file):
        project_directory = filedialog.askdirectory(title="请选择工程目录")
        if project_directory:
            config['project_directory'] = project_directory
            with open(config_file, 'w') as file:
                yaml.dump(config, file)
    else:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
            project_directory = config.get('project_directory')
            if not project_directory:
                messagebox.showerror("错误", "配置文件中未找到工程目录")

    if 'openeprj_cmd' not in config:
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"LCEDA.Library.File\shell\open\commanda") as key:
                openeprj_cmd = winreg.QueryValue(key, None)
                config['openeprj_cmd'] = openeprj_cmd
        except FileNotFoundError:
            lceda_pro_path = filedialog.askopenfilename(title="请选择立创EDA（lceda-pro.exe）安装位置", filetypes=[("嘉立创EDA", "lceda-pro.exe")])
            if lceda_pro_path:
                config['openeprj_cmd'] = f'"{lceda_pro_path}" "%1"'
            else:
                messagebox.showwarning("警告", "未选择lceda-pro.exe安装位置，需要选择lceda-pro.exe安装位置后才能打开工程")

        with open(config_file, 'w') as file:
            yaml.dump(config, file)

    return project_directory


def reselect_project_directory():
    project_directory = filedialog.askdirectory(title="请选择工程目录")
    if project_directory:
        with open('config.yaml', 'w') as file:
            yaml.dump({'project_directory': project_directory}, file)
        global directory
        directory = project_directory
        populate_listbox(eprj_listbox, list_eprj_files(directory))
        root.title("嘉立创EDA工程管理工具" + " - " + directory)


def list_eprj_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.eprj')]


def populate_listbox(listbox, items):
    listbox.delete(0, tk.END)
    for item in items:
        listbox.insert(tk.END, item)


def on_double_click_listbox(event):
    selected_file = event.widget.get(event.widget.curselection())
    global db_path
    db_path = os.path.join(directory, selected_file)
    display_tree_structure(db_path)


def on_double_click_treeview(event):
    selected_item = eprj_treeview.selection()[0]
    item_text = eprj_treeview.item(selected_item, "text")
    if " (UUID:" in item_text:
        title, uuid = item_text.split(" (UUID:")
        uuid = uuid.rstrip(")")
        display_image(uuid, db_path, title.strip())


def on_details_click():
    def copy_to_clipboard(event):
        selected_items = treeview.selection()
        if selected_items:
            clipboard_text = ""
            for item in selected_items:
                item_values = treeview.item(item, "values")
                clipboard_text += f"{item_values[0]}: {item_values[1]}\n"
            top.clipboard_clear()
            top.clipboard_append(clipboard_text.strip())
            top.update()

    top = Toplevel()
    top.title("工程详细信息")
    top.geometry("300x400")
    top.resizable(False, False)
    top.iconbitmap(icon_path)

    frame = ttk.Frame(top, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)

    columns = ("key", "value")
    treeview = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
    treeview.pack(fill=tk.BOTH, expand=True)

    treeview.heading("key", text="项目")
    treeview.heading("value", text="值")
    treeview.column("key", width=50)
    treeview.column("value", width=100)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT uuid, name, owner_uuid, creator_uuid, modifier_uuid, updated_at, created_at FROM projects")
        rows = cursor.fetchall()
        for row in rows:
            treeview.insert("", tk.END, values=("UUID", row[0]))
            treeview.insert("", tk.END, values=("名称", row[1]))
            treeview.insert("", tk.END, values=("所有者", row[2]))
            treeview.insert("", tk.END, values=("创建者", row[3]))
            treeview.insert("", tk.END, values=("修改者", row[4]))
            treeview.insert("", tk.END, values=("更新于", row[5]))
            treeview.insert("", tk.END, values=("创建于", row[6]))

        cursor.execute("SELECT COUNT(*) FROM devices")
        device_count = cursor.fetchone()[0]
        treeview.insert("", tk.END, values=("包含器件数", device_count))

        cursor.execute("SELECT COUNT(*) FROM resources")
        resource_count = cursor.fetchone()[0]
        treeview.insert("", tk.END, values=("包含资源数", resource_count))
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

    top.bind_all("<Control-c>", copy_to_clipboard)


def display_image(uuid, db_path, title):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM documents WHERE uuid=? OR schematic_uuid=?", (uuid, uuid))
        image_data = cursor.fetchone()
        if image_data and image_data[0]:
            image_data = image_data[0]
            if image_data.startswith("data:image/webp;base64,"):
                image_data = image_data[len("data:image/webp;base64,"):]
            image = Image.open(io.BytesIO(base64.b64decode(image_data)))

            top = Toplevel()
            top.title(f"{title} - {uuid}")

            screen_width = top.winfo_screenwidth()
            screen_height = top.winfo_screenheight()
            window_width = screen_width // 2
            window_height = screen_height // 2
            top.geometry(f"{window_width}x{window_height}")
            top.resizable(True, True)
            top.iconbitmap(icon_path)

            canvas = Canvas(top, bg='white')
            canvas.pack(fill=tk.BOTH, expand=True)

            img_width, img_height = image.size
            scale = 1.0

            def zoom(event):
                nonlocal scale
                if event.delta > 0:
                    scale *= 1.1
                elif event.delta < 0:
                    scale /= 1.1
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                resized_image = image.resize((new_width, new_height), Image.LANCZOS)
                image_tk = ImageTk.PhotoImage(resized_image)
                canvas.image = image_tk
                canvas.create_image(0, 0, anchor=tk.NW, image=image_tk)
                canvas.config(scrollregion=canvas.bbox(tk.ALL))

            def move_image(event):
                canvas.scan_dragto(event.x, event.y, gain=1)

            canvas.bind("<MouseWheel>", zoom)
            canvas.bind("<B1-Motion>", move_image)
            canvas.bind("<ButtonPress-1>", lambda event: canvas.scan_mark(event.x, event.y))

            image_tk = ImageTk.PhotoImage(image)
            canvas.image = image_tk
            canvas.create_image(0, 0, anchor=tk.NW, image=image_tk)
            canvas.config(scrollregion=canvas.bbox(tk.ALL))
        else:
            messagebox.showwarning("警告", "无法预览该文档，请在嘉立创EDA重新保存该文档")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()


def display_tree_structure(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT boards FROM projects;")
    boards_data = cursor.fetchone()
    if boards_data:
        boards = json.loads(boards_data[0])

        cursor.execute("SELECT uuid, display_title, docType FROM documents;")
        documents = cursor.fetchall()
        documents_pcb_dict = {doc[0]: doc[1] for doc in documents if doc[2] == 3}
        documents_sch_dict = {doc[0]: doc[1] for doc in documents if doc[2] == 1}
        documents_other_dict = {doc[0]: doc[1] for doc in documents if doc[2] not in [1, 3]}

        cursor.execute("SELECT uuid, display_name, sort FROM schematics;")
        schematics = cursor.fetchall()
        schematic_dict = {sch[0]: sch[1] for sch in schematics}
        schematic_sort_dict = {}
        for sch in schematics:
            try:
                schematic_sort_dict[sch[0]] = sch[2].split(',')
            except Exception as e:
                print(f"Error parsing sort data for schematic {sch[0]}: {e}")
                schematic_sort_dict[sch[0]] = []

        for item in eprj_treeview.get_children():
            eprj_treeview.delete(item)

        displayed_uuids = set()
        for board in boards:
            board_name = board['name']
            sch_uuid = board['sch']
            pcb_uuid = board['pcb']
            sch_title = schematic_dict.get(sch_uuid)
            pcb_title = documents_pcb_dict.get(pcb_uuid)
            board_item = eprj_treeview.insert("", "end", text=board_name)
            if sch_title:
                sch_item = eprj_treeview.insert(board_item, "end", text=f"[SCH] {sch_title} (UUID:{sch_uuid})")
                displayed_uuids.add(sch_uuid)
                for child_uuid in schematic_sort_dict.get(sch_uuid, []):
                    child_title = documents_sch_dict.get(child_uuid)
                    if child_title:
                        eprj_treeview.insert(sch_item, "end", text=f"{child_title} (UUID:{child_uuid})")
            if pcb_title:
                eprj_treeview.insert(board_item, "end", text=f"[PCB] {pcb_title} (UUID:{pcb_uuid})")
                displayed_uuids.add(pcb_uuid)

        for uuid, title in documents_pcb_dict.items():
            if uuid not in displayed_uuids:
                eprj_treeview.insert("", "end", text=f"[PCB] {title} (UUID:{uuid})")

        for uuid, title in schematic_dict.items():
            if uuid not in displayed_uuids:
                eprj_treeview.insert("", "end", text=f"[SCH] {title} (UUID:{uuid})")

        for uuid, title in documents_other_dict.items():
            if uuid not in displayed_uuids:
                eprj_treeview.insert("", "end", text=f"{title} (UUID:{uuid})")

    conn.close()


def on_delete_click():
    selected_items = eprj_listbox.curselection()
    if not selected_items:
        messagebox.showwarning("警告", "请选择一个或多个工程进行删除")
        return

    for selected_item in selected_items:
        selected_file = eprj_listbox.get(selected_item)
        project_path = os.path.join(directory, selected_file)
        backup_path = project_path.replace('.eprj', '_backup')

        wastebasket_path = os.path.join(directory, '.wastebasket')
        if not os.path.exists(wastebasket_path):
            os.makedirs(wastebasket_path)

        target_path = os.path.join(wastebasket_path, selected_file)
        if os.path.exists(target_path):
            messagebox.showwarning("错误", f"删除工程时出错: 目标路径 '{target_path}' 已存在，跳过该文件")
            continue

        try:
            shutil.move(project_path, wastebasket_path)
            if os.path.exists(backup_path):
                shutil.move(backup_path, wastebasket_path)
        except Exception as e:
            messagebox.showerror("错误", f"删除工程时出错: {e}")

    populate_listbox(eprj_listbox, list_eprj_files(directory))
    # messagebox.showinfo("信息", "项目已成功删除")


def on_open_click():
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
        openeprj_cmd = config.get('openeprj_cmd')
        if openeprj_cmd:
            selected_items = eprj_listbox.curselection()
            if not selected_items:
                messagebox.showwarning("警告", "请选择一个工程进行打开")
                return
            selected_file = eprj_listbox.get(selected_items[0])
            file_to_open = os.path.join(directory, selected_file)
            try:
                os.startfile(file_to_open)
            except Exception as e:
                messagebox.showerror("错误", f"打开文件时出错: {e}")
        else:
            messagebox.showwarning("警告", "无法打开工程，未找到lceda-pro.exe安装位置")
            lceda_pro_path = filedialog.askopenfilename(title="请选择立创EDA（lceda-pro.exe）安装位置", filetypes=[("嘉立创EDA", "lceda-pro.exe")])
            if lceda_pro_path:
                config['openeprj_cmd'] = f'"{lceda_pro_path}" "%1"'
                with open('config.yaml', 'w') as file:
                    yaml.dump(config, file)
            else:
                messagebox.showwarning("错误", "未选择lceda-pro.exe安装位置，需要选择lceda-pro.exe安装位置后才能打开工程")


def open_tools_windows():
    top = Toplevel()
    top.title("小工具")
    top.geometry("400x400")
    top.resizable(False, False)
    top.iconbitmap(icon_path)

    frame = ttk.Frame(top, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)

    def open_imagetool():
        imagetool = Toplevel()
        imagetool.title("预览图批量导出工具")
        imagetool.geometry("260x400")
        imagetool.resizable(False, False)
        imagetool.iconbitmap(icon_path)

        imagetool_frame = ttk.Frame(imagetool, padding="10")
        imagetool_frame.pack(fill=tk.BOTH, expand=True)

        # 列表框
        listbox_frame = ttk.Frame(imagetool_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        listbox_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical")
        listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        eprj_listbox = tk.Listbox(listbox_frame, selectmode=tk.EXTENDED, yscrollcommand=listbox_scrollbar.set)
        eprj_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        listbox_scrollbar.config(command=eprj_listbox.yview)

        # 列出所有工程
        eprj_files = list_eprj_files(directory)
        for file in eprj_files:
            eprj_listbox.insert(tk.END, file)

        # 复选框
        sch_var = tk.BooleanVar()
        pcb_var = tk.BooleanVar()

        sch_checkbox = ttk.Checkbutton(imagetool_frame, text="SCH", variable=sch_var)
        sch_checkbox.pack(side=tk.LEFT, padx=5, pady=5)

        pcb_checkbox = ttk.Checkbutton(imagetool_frame, text="PCB", variable=pcb_var)
        pcb_checkbox.pack(side=tk.LEFT, padx=5, pady=5)

        # 导出按钮的函数
        def export_selected():
            selected_files = [eprj_listbox.get(i) for i in eprj_listbox.curselection()]
            export_sch = sch_var.get()
            export_pcb = pcb_var.get()

            if not selected_files:
                messagebox.showwarning("警告", "请选择一个或多个工程进行导出")
                return

            export_directory = filedialog.askdirectory(title="请选择导出目录")
            if not export_directory:
                messagebox.showwarning("警告", "未选择导出目录")
                return

            missing_images = []

            progress_window = Toplevel()
            progress_window.title("导出进度")
            progress_window.geometry("300x100")
            progress_window.resizable(False, False)
            progress_window.iconbitmap(icon_path)

            progress_label = ttk.Label(progress_window, text="正在导出...")
            progress_label.pack(pady=10)

            progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=200, mode="determinate")
            progress_bar.pack(pady=10)

            total_files = len(selected_files)
            progress_bar["maximum"] = total_files

            for index, file in enumerate(selected_files):
                db_path = os.path.join(directory, file)
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    name = file.replace('.eprj', '')

                    if export_sch:
                        cursor.execute("SELECT display_title, image FROM documents WHERE docType = 1")
                        rows = cursor.fetchall()
                        for row in rows:
                            display_title, image_data = row
                            if image_data:
                                save_image(export_directory, "SCH", name, display_title, image_data)
                            else:
                                missing_images.append((file, display_title, "SCH"))

                    if export_pcb:
                        cursor.execute("SELECT display_title, image FROM documents WHERE docType = 3")
                        rows = cursor.fetchall()
                        for row in rows:
                            display_title, image_data = row
                            if image_data:
                                save_image(export_directory, "PCB", name, display_title, image_data)
                            else:
                                missing_images.append((file, display_title, "PCB"))

                except sqlite3.Error as e:
                    messagebox.showerror("错误", f"数据库错误: {e}")
                except Exception as e:
                    messagebox.showerror("错误", f"导出时出错: {e}")
                finally:
                    conn.close()

                progress_bar["value"] = index + 1
                progress_window.update_idletasks()

            progress_window.destroy()

            if missing_images:
                missing_images_str = "\n".join([f"{file} - {display_title} ({doc_type})" for file, display_title, doc_type in missing_images])
                messagebox.showwarning("警告", f"以下文档没有图片数据，请在嘉立创 EDA 保存一次后再试！\n{missing_images_str}")

        def save_image(directory, doc_type, name, display_title, image_data):
            if image_data.startswith("data:image/webp;base64,"):
                image_data = image_data[len("data:image/webp;base64,"):]
            image = Image.open(io.BytesIO(base64.b64decode(image_data)))
            file_path = os.path.join(directory, f"[{doc_type}]{name}.{display_title}.png")
            image.save(file_path, "PNG")

        export_button = ttk.Button(imagetool_frame, text="导出", command=export_selected)
        export_button.pack(side=tk.BOTTOM, pady=10)

    open_imagetool_button = ttk.Button(frame, text="预览图批量导出", command=open_imagetool, style='info.TButton')
    open_imagetool_button.pack(side=tk.TOP, padx=5)

def on_open_wastebasket_click():
    wastebasket_path = os.path.join(directory, '.wastebasket')

    top = Toplevel()
    top.title("回收站")
    top.geometry("260x400")
    top.resizable(False, False)
    top.iconbitmap(icon_path)

    frame = ttk.Frame(top, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)

    listbox = tk.Listbox(frame)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)

    eprj_files = [f for f in os.listdir(wastebasket_path) if f.endswith('.eprj')]
    for file in eprj_files:
        listbox.insert(tk.END, file)

    button_frame = ttk.Frame(top, padding="10")
    button_frame.pack(fill=tk.X)

    def restore_file():
        selected_item = listbox.curselection()
        if not selected_item:
            messagebox.showwarning("警告", "请选择一个工程进行还原")
            return

        selected_file = listbox.get(selected_item)
        project_path = os.path.join(wastebasket_path, selected_file)
        backup_path = project_path.replace('.eprj', '_backup')
        target_path = os.path.join(directory, selected_file)
        target_backup_path = target_path.replace('.eprj', '_backup')

        try:
            shutil.move(project_path, target_path)
            if os.path.exists(backup_path):
                shutil.move(backup_path, target_backup_path)
            listbox.delete(selected_item)
            populate_listbox(eprj_listbox, list_eprj_files(directory))
            # messagebox.showinfo("信息", "项目已成功还原")
        except Exception as e:
            messagebox.showerror("错误", f"还原工程时出错: {e}")

    def delete_file():
        selected_item = listbox.curselection()
        if not selected_item:
            messagebox.showwarning("警告", "请选择一个工程进行删除")
            return

        selected_file = listbox.get(selected_item)
        project_path = os.path.join(wastebasket_path, selected_file)
        backup_path = project_path.replace('.eprj', '_backup')

        try:
            os.remove(project_path)
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            listbox.delete(selected_item)
            messagebox.showinfo("信息", "项目已永久删除")
        except Exception as e:
            messagebox.showerror("错误", f"删除工程时出错: {e}")

    restore_button = ttk.Button(button_frame, text="还原", command=restore_file, style='success.TButton')
    restore_button.pack(side=tk.LEFT, padx=5)

    delete_button = ttk.Button(button_frame, text="删除", command=delete_file, style='danger.TButton')
    delete_button.pack(side=tk.LEFT, padx=5)


def main():
    global eprj_listbox, eprj_treeview, directory, root
    root = tk.Tk()
    root.title("嘉立创EDA工程管理工具")
    root.geometry("800x400")
    root.resizable(False, False)
    root.iconbitmap(icon_path)

    Style(theme='flatly').theme_use()

    frame = ttk.Frame(root, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)

    left_frame = ttk.Frame(frame, padding="10")
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    right_frame = ttk.Frame(frame, padding="10")
    right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    left_frame.pack_propagate(False)
    left_frame.config(width=100)
    right_frame.pack_propagate(False)
    right_frame.config(width=300)

    left_scrollbar = ttk.Scrollbar(left_frame)
    left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    eprj_listbox = tk.Listbox(left_frame, yscrollcommand=left_scrollbar.set, selectmode=tk.EXTENDED)
    eprj_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    eprj_listbox.bind("<Double-1>", on_double_click_listbox)

    left_scrollbar.config(command=eprj_listbox.yview)

    right_top_frame = ttk.Frame(right_frame, padding="10")
    right_top_frame.pack(side=tk.TOP, fill=tk.X)

    right_bottom_frame = ttk.Frame(right_frame, padding="10")
    right_bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    delete_button = ttk.Button(right_top_frame, text="删除", command=on_delete_click, style='danger.TButton')
    delete_button.pack(side=tk.LEFT, padx=5)

    open_project_button = ttk.Button(right_top_frame, text="打开", command=on_open_click, style='success.TButton')
    open_project_button.pack(side=tk.LEFT, padx=5)

    details_button = ttk.Button(right_top_frame, text="详细", command=on_details_click, style='success.TButton')
    details_button.pack(side=tk.LEFT, padx=5)

    open_wastebasket_button = ttk.Button(right_top_frame, text="回收站", command=on_open_wastebasket_click, style='info.TButton')
    open_wastebasket_button.pack(side=tk.LEFT, padx=5)

    reselect_project_button = ttk.Button(right_top_frame, text="选择目录", command=reselect_project_directory, style='info.TButton')
    reselect_project_button.pack(side=tk.LEFT, padx=5)

    open_tools_button = ttk.Button(right_top_frame, text="小工具", command=open_tools_windows, style='info.TButton')
    open_tools_button.pack(side=tk.LEFT, padx=5)

    eprj_treeview = ttk.Treeview(right_bottom_frame, show="tree")
    eprj_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    eprj_treeview.bind("<Double-1>", on_double_click_treeview)

    right_scrollbar = ttk.Scrollbar(right_bottom_frame, orient="vertical", command=eprj_treeview.yview)
    right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    eprj_treeview.configure(yscrollcommand=right_scrollbar.set)

    def on_root_loaded():
        global directory
        directory = get_project_directory()
        eprj_files = list_eprj_files(directory)
        populate_listbox(eprj_listbox, eprj_files)
        root.title("嘉立创EDA工程管理工具" + " - " + directory)

    root.after(100, on_root_loaded)
    root.mainloop()


if __name__ == "__main__":
    main()
