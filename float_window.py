import tkinter as tk
from tkinter import font
import threading
import logging


class FloatWindow:
    def __init__(self, usage_tracker):
        self.logger = logging.getLogger("FloatWindow")
        self.usage_tracker = usage_tracker
        self.root = None
        self.time_label = None
        self.running = False

    def create_window(self):
        """创建浮动窗口"""
        self.root = tk.Tk()
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
            text=f"今日使用: {self.format_time(self.usage_tracker.get_usage_time())}",
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

        # 右键菜单 - 退出
        # def exit_program():
        #     self.usage_tracker.save_usage_stats()
        #     self.root.destroy()
        #     self.running = False
        #
        # def create_menu(event):
        #     menu = tk.Menu(self.root, tearoff=0)
        #     menu.add_command(label="退出", command=exit_program)
        #     menu.post(event.x_root, event.y_root)
        #
        # self.time_label.bind("<Button-3>", create_menu)

        # 初始位置
        screen_width = self.root.winfo_screenwidth()
        window_width = 320  # 设置窗口宽度，根据实际内容调整
        x_position = (screen_width - window_width) // 2  # 计算居中位置
        self.root.geometry(f"{window_width}x50+{x_position}+0")  # 设置窗口大小和位置

        # 更新时间显示
        def update_time():
            if self.time_label:
                current_time = self.format_time(self.usage_tracker.get_usage_time())
                self.time_label.config(text=f"今日使用: {current_time}")
                self.logger.debug(f"Updated float window time: {current_time}")
            self.root.after(1000, update_time)  # 每秒更新一次

        update_time()

    def format_time(self, seconds):
        """将秒数格式化为HH:MM:SS格式"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def run(self):
        """运行浮动窗口主循环"""
        self.running = True
        self.logger.info("Float window started")

        try:
            self.create_window()
            self.root.mainloop()
        except Exception as e:
            self.logger.critical(f"Error in float window: {str(e)}")
        finally:
            self.running = False
            self.logger.info("Float window stopped")