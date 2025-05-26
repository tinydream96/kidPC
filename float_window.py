import tkinter as tk
from tkinter import font
import threading
import logging
import time  # 确保导入 time 模块


class FloatWindow:
    def __init__(self, master_root, usage_tracker):  # 接收主 Tkinter 根窗口
        self.logger = logging.getLogger("FloatWindow")
        self.usage_tracker = usage_tracker
        self.root = None
        self.time_label = None
        self.running = False
        self.master_root = master_root  # 存储主根窗口的引用

    def create_window(self):
        """创建浮动窗口 (现在是 Toplevel 窗口)"""
        # 检查是否已经创建，避免重复创建
        if self.root and self.root.winfo_exists():
            self.logger.info("Float window already exists, skipping creation.")
            return

        self.root = tk.Toplevel(self.master_root)  # 使用 Toplevel，并指定父窗口
        self.root.title("电脑使用时间")

        # 设置窗口属性
        self.root.attributes('-alpha', 0.7)  # 透明度
        self.root.attributes('-topmost', True)  # 置顶
        self.root.overrideredirect(True)  # 无边框

        # 设置字体
        display_font = font.Font(family="微软雅黑", size=24, weight="bold")

        # 创建时间标签
        self.time_label = tk.Label(
            self.root,
            text=f"今日使用: {self.usage_tracker.format_time(self.usage_tracker.get_usage_time())}",
            font=display_font,
            bg="#333333",
            fg="white",
            padx=10,
            pady=5
        )
        self.time_label.pack()

        # 绑定鼠标事件 - 拖动窗口
        def on_drag_start(event):
            self.root.x = event.x
            self.root.y = event.y

        def on_drag_motion(event):
            x = self.root.winfo_pointerx() - self.root.x - self.root.winfo_rootx()
            y = self.root.winfo_pointery() - self.root.y - self.root.winfo_rooty()
            self.root.geometry(f"+{x}+{y}")

        self.time_label.bind("<Button-1>", on_drag_start)
        self.time_label.bind("<B1-Motion>", on_drag_motion)

        # 窗口关闭协议（Toplevel 窗口的 destroy）
        self.root.protocol("WM_DELETE_WINDOW", self.stop)

        # 初始位置
        screen_width = self.root.winfo_screenwidth()
        window_width = 320
        x_position = (screen_width - window_width) // 2
        self.root.geometry(f"{window_width}x50+{x_position}+0")

        self.update_time()  # 首次调用更新时间

        self.logger.info("Float window Toplevel created.")

    def update_time(self):
        """更新时间显示"""
        if self.time_label and self.running and self.root and self.root.winfo_exists():  # 增加检查窗口是否存在
            current_time = self.usage_tracker.format_time(self.usage_tracker.get_usage_time())
            self.time_label.config(text=f"今日使用: {current_time}")
            self.logger.debug(f"Updated float window time: {current_time}")
            self.root.after(1000, self.update_time)  # 每秒更新一次
        elif self.time_label and self.running and (not self.root or not self.root.winfo_exists()):
            # 如果窗口不存在，但running是True，说明窗口被外部关闭了，停止更新
            self.logger.info("Float window no longer exists, stopping updates.")
            self.running = False

    def run(self):
        """运行浮动窗口线程逻辑，在主线程中创建窗口"""
        self.running = True
        self.logger.info("Float window thread started.")
        # 在主 Tkinter 线程中调度窗口创建
        self.master_root.after(0, self.create_window)

        # 这个循环现在只是保持线程活跃，直到 stop() 被调用
        while self.running:
            time.sleep(1)  # 简单休眠，不阻塞主UI线程

    def stop(self):
        self.running = False
        if self.root and self.root.winfo_exists():  # 检查窗口是否存在
            self.root.destroy()  # 销毁 Toplevel 窗口
            self.root = None
        self.time_label = None  # 清空引用
        self.logger.info("FloatWindow thread stopped.")

    # 移除 format_time 方法，因为 UsageTracker 已经有了
    # def format_time(self, seconds):
    #     hours, remainder = divmod(int(seconds), 3600)
    #     minutes, seconds = divmod(remainder, 60)
    #     return f"{hours:02d}:{minutes:02d}:{seconds:02d}"