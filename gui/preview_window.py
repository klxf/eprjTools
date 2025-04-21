import tkinter as tk
from tkinter import ttk, Canvas
from PIL import Image, ImageTk
import base64
import io


class DocumentPreviewWindow:
    def __init__(self, parent, title, uuid, image_data):
        self.top = tk.Toplevel(parent) if parent else tk.Toplevel()
        self.top.title(f"{title} - {uuid}")

        # 设置窗口大小为屏幕的一半
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        window_width = screen_width // 2
        window_height = screen_height // 2
        self.top.geometry(f"{window_width}x{window_height}")
        self.top.resizable(True, True)

        # 创建画布
        self.canvas = Canvas(self.top, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 加载图片
        self.load_image(image_data)

        # 绑定事件
        self.bind_events()

    def load_image(self, image_data):
        if image_data.startswith("data:image/webp;base64,"):
            image_data = image_data[len("data:image/webp;base64,"):]

        # 解码和加载图片
        image_bytes = base64.b64decode(image_data)
        self.original_image = Image.open(io.BytesIO(image_bytes))
        self.img_width, self.img_height = self.original_image.size
        self.scale = 1.0

        # 显示图片
        self.update_image()

    def update_image(self):
        new_width = int(self.img_width * self.scale)
        new_height = int(self.img_height * self.scale)
        resized_image = self.original_image.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )

        self.image_tk = ImageTk.PhotoImage(resized_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def bind_events(self):
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonPress-1>", self.on_press)

    def on_mousewheel(self, event):
        if event.delta > 0:
            self.scale *= 1.1
        else:
            self.scale /= 1.1
        self.update_image()

    def on_press(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def on_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)