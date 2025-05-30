import tkinter as tk
from tkinter import font
import threading
import logging
import time
from typing import Optional
from usage_tracker import UsageTracker


class FloatWindow:
    logger: logging.Logger
    usage_tracker: UsageTracker
    root: Optional[tk.Toplevel]
    time_label: Optional[tk.Label]
    running: bool
    master_root: tk.Tk

    # 为拖动功能添加实例变量类型提示
    _drag_x: int
    _drag_y: int

    def __init__(self, master_root: tk.Tk, usage_tracker: UsageTracker) -> None:
        self.logger = logging.getLogger("FloatWindow")
        self.usage_tracker = usage_tracker
        self.root = None
        self.time_label = None
        self.running = False
        self.master_root = master_root
        self._drag_x = 0 # Initialize drag coordinates
        self._drag_y = 0 # Initialize drag coordinates

    def create_window(self) -> None:
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
        def on_drag_start(event: tk.Event) -> None:
            # Store initial mouse click position relative to the window
            self._drag_x = event.x
            self._drag_y = event.y

        def on_drag_motion(event: tk.Event) -> None:
            # Calculate new window position based on mouse movement
            # event.x_root and event.y_root are screen coordinates of the mouse
            # self.root.winfo_x() and self.root.winfo_y() are current window top-left
            # No, this original logic was a bit off. Let's correct it.
            # The new top-left corner (x, y) of the window should be:
            # current_mouse_screen_x - initial_click_offset_x
            # current_mouse_screen_y - initial_click_offset_y
            if self.root: # Ensure root exists
                x = self.root.winfo_pointerx() - self._drag_x
                y = self.root.winfo_pointery() - self._drag_y
                self.root.geometry(f"+{x}+{y}")

        if self.time_label: # Ensure time_label exists before binding
            self.time_label.bind("<Button-1>", on_drag_start)
            self.time_label.bind("<B1-Motion>", on_drag_motion)

        if self.root: # Ensure root exists before setting protocol or geometry
            # 窗口关闭协议（Toplevel 窗口的 destroy）
            self.root.protocol("WM_DELETE_WINDOW", self.stop)

            # 初始位置
            screen_width = self.root.winfo_screenwidth()
            window_width = 320 # Assuming a fixed width for calculation
            # Ensure window_width is calculated or fetched if dynamic
            # For instance, self.root.update_idletasks(); window_width = self.root.winfo_width();
            x_position = (screen_width - window_width) // 2
            self.root.geometry(f"{window_width}x50+{x_position}+0") # Assuming height 50

            self.update_time()  # 首次调用更新时间
            self.logger.info("Float window Toplevel created.")
        else:
            self.logger.error("Root window was not created, cannot complete setup.")


    def update_time(self) -> None:
        """更新时间显示"""
        if self.time_label and self.running and self.root and self.root.winfo_exists():
            current_usage_seconds = self.usage_tracker.get_usage_time()
            current_time_formatted = self.usage_tracker.format_time(current_usage_seconds)
            self.time_label.config(text=f"今日使用: {current_time_formatted}")
            self.logger.debug(f"Updated float window time: {current_time_formatted}")
            self.root.after(1000, self.update_time)
        elif self.running and (not self.root or not self.root.winfo_exists()):
            self.logger.info("Float window no longer exists or not running, stopping updates.")
            self.running = False

    def run(self) -> None:
        """运行浮动窗口线程逻辑，在主线程中创建窗口"""
        if not isinstance(self.master_root, tk.Tk) or not self.master_root.winfo_exists():
            self.logger.error("Master root is not a valid Tk window or has been destroyed. Cannot run FloatWindow.")
            return

        self.running = True
        self.logger.info("Float window thread started.")
        self.master_root.after(0, self.create_window)

        while self.running:
            try:
                # Check if master_root is still valid, otherwise stop thread
                if not self.master_root.winfo_exists():
                    self.logger.warning("Master root window destroyed, stopping FloatWindow thread.")
                    self.stop()
                    break
                time.sleep(1)
            except tk.TclError as e:
                self.logger.error(f"TclError in FloatWindow run loop (master_root likely destroyed): {e}")
                self.stop()
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in FloatWindow run loop: {e}")
                self.stop() # Stop on other critical errors too
                break


    def stop(self) -> None:
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