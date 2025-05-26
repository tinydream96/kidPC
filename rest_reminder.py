import tkinter as tk
from tkinter import messagebox
import time
import datetime
import os
import threading
import sys
import logging


# import configparser # 不需要单独导入，通过 config_manager 访问

class RestReminder:
    # 接收主 Tkinter 根窗口和 ConfigManager 实例
    def __init__(self, main_root, config_manager, usage_tracker=None):
        self.logger = logging.getLogger("RestReminder")  # 统一日志获取方式
        self.shutdown_scheduled = False
        self.shutdown_time = None
        self.root = None  # 用于提醒窗口的 Toplevel 实例
        self.usage_tracker = usage_tracker
        self.window_open = False  # 跟踪窗口状态
        self.main_root = main_root  # 存储主 Tkinter 根窗口的引用

        self.config_manager = config_manager  # 存储 ConfigManager 实例

        # 从 ConfigManager 获取参数
        self.first_reminder_hour = self.config_manager.get_setting('Settings', 'firstReminderHour', type=int,
                                                                   fallback=21)
        self.shutdown_plan_hour = self.config_manager.get_setting('Settings', 'shutdownPlanHour', type=int, fallback=21)
        self.shutdown_plan_minute = self.config_manager.get_setting('Settings', 'shutdownPlanMinute', type=int,
                                                                    fallback=30)
        self.shutdown_delay_minutes = self.config_manager.get_setting('Settings', 'shutdownDelayMinutes', type=int,
                                                                      fallback=5)
        self.reminder_interval_seconds = self.config_manager.get_setting('Settings', 'reminderIntervalSeconds',
                                                                         type=int, fallback=300)
        self.continuous_usage_threshold = self.config_manager.get_setting('Settings', 'continuousUsageThreshold',
                                                                          type=int, fallback=10) * 60  # 默认为10分钟
        self.forced_rest_duration = self.config_manager.get_setting('Settings', 'forcedRestDuration', type=int,
                                                                    fallback=1) * 60  # 默认为1分钟
        self.forced_shutdown_hour = self.config_manager.get_setting('Settings', 'forcedShutdownHour', type=int,
                                                                    fallback=22)

        self.logger.info("RestReminder initialized with settings from ConfigManager.")

    # 移除 setup_logger 方法，因为已经在 main.py 中统一配置了
    # def setup_logger(self):
    #     """配置日志记录"""
    #     # ... (此方法被移除) ...

    def check_time(self):
        # ... (保持不变) ...
        now = datetime.datetime.now()
        first_reminder_time = now.replace(hour=self.first_reminder_hour, minute=0, second=0, microsecond=0)
        shutdown_plan_time = now.replace(hour=self.shutdown_plan_hour, minute=self.shutdown_plan_minute,
                                         second=0, microsecond=0)
        forced_shutdown_time = now.replace(hour=self.forced_shutdown_hour, minute=0, second=0, microsecond=0)

        return now >= first_reminder_time, now >= shutdown_plan_time, now >= forced_shutdown_time

    def show_reminder_window(self, is_shutdown=False, countdown=300):
        """显示提醒窗口"""
        if self.window_open:
            self.logger.info("提醒窗口已打开，跳过显示")
            return

        # 在主线程中调度窗口创建
        self.main_root.after(0, lambda: self._create_reminder_window(is_shutdown, countdown))

    def _create_reminder_window(self, is_shutdown=False, countdown=300):
        if self.window_open:  # 再次检查，防止多重调度
            return

        self.window_open = True
        self.root = tk.Toplevel(self.main_root)  # 使用 Toplevel
        self.root.title("休息提醒")
        self.root.attributes('-topmost', True)
        self.root.geometry("600x400")
        self.root.configure(bg="#FF6B6B")

        title_font = ("微软雅黑", 36, "bold")
        content_font = ("微软雅黑", 24)

        title_label = tk.Label(self.root, text="该休息啦！", font=title_font, bg="#FF6B6B", fg="white")
        title_label.pack(pady=40)

        if is_shutdown:
            content = f"电脑将在 {countdown // 60} 分钟后自动关机\n请保存好您的工作！"
        else:
            content = "已经很晚了，请注意休息！\n长时间使用电脑会影响健康。"

        content_label = tk.Label(self.root, text=content, font=content_font, bg="#FF6B6B", fg="white", wraplength=500)
        content_label.pack(pady=20)

        button_frame = tk.Frame(self.root, bg="#FF6B6B")
        button_frame.pack(pady=30)

        if is_shutdown:
            cancel_button = tk.Button(button_frame, text="取消关机", font=("微软雅黑", 18), bg="#FFD166", fg="#2A2A2A",
                                      width=15, command=self.cancel_shutdown)
            cancel_button.pack()
            self.update_countdown(countdown)  # 启动倒计时更新
        else:
            ok_button = tk.Button(button_frame, text="知道了", font=("微软雅黑", 18), bg="#06D6A0", fg="white",
                                  width=15, command=self.close_window)
            ok_button.pack()

        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        # 不再调用 mainloop，让主程序的 mainloop 管理这个 Toplevel 窗口

    def show_forced_rest_window(self, countdown=300):
        """显示强制休息窗口"""
        if self.window_open:
            self.logger.info("强制休息窗口已打开，跳过显示")
            return

        # 在主线程中调度窗口创建
        self.main_root.after(0, lambda: self._create_forced_rest_window(countdown))

    def _create_forced_rest_window(self, countdown=300):
        if self.window_open:  # 再次检查
            return

        self.window_open = True
        self.root = tk.Toplevel(self.main_root)  # 使用 Toplevel
        self.root.title("强制休息提醒")

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        self.root.attributes('-topmost', True)
        self.root.configure(bg="#C2F0C2")
        self.root.resizable(width=False, height=False)
        self.root.overrideredirect(True)

        title_font = ("微软雅黑", int(screen_height / 10), "bold")
        content_font = ("微软雅黑", int(screen_height / 20))

        title_label = tk.Label(self.root, text="强制休息！", font=title_font, bg="#C2F0C2", fg="white")
        title_label.pack(pady=int(screen_height * 0.1))

        content = f"您已连续使用电脑{self.continuous_usage_threshold // 60}分钟，请休息 {countdown // 60} 分钟！"
        content_label = tk.Label(self.root, text=content, font=content_font, bg="#C2F0C2", fg="white",
                                 wraplength=screen_width * 0.8)
        content_label.pack(pady=int(screen_height * 0.05))

        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.update_forced_rest_countdown(countdown)
        # 不再调用 mainloop

    def close_window(self):
        """安全关闭窗口，确保在主线程中执行"""
        if self.root and self.window_open:
            self.logger.info("关闭窗口请求")
            # 在主线程中执行销毁操作
            self.main_root.after(0, self._perform_close_window)

    def _perform_close_window(self):
        if self.root and self.window_open:
            try:
                self.root.destroy()
                self.logger.info("窗口已销毁")
            except Exception as e:
                self.logger.error(f"销毁窗口时出错: {e}")
            self.root = None
            self.window_open = False

    def update_forced_rest_countdown(self, seconds):
        # ... (保持不变，但确保内部对 self.root 的操作在主线程) ...
        # Tkinter 的 after 方法会自动在创建 after 调用的那个线程的 mainloop 中执行
        # 因为 show_forced_rest_window 内部通过 self.main_root.after(0, ...) 调度了 _create_forced_rest_window
        # 所以这里的 after 也会在 main_root 的 mainloop 中执行，是安全的
        if not self.root or not self.root.winfo_exists() or not self.window_open:
            return

        if seconds <= 0:
            self.close_window()
            if self.usage_tracker:
                self.usage_tracker.reset_continuous_usage_time()
            return

        content = f"您已连续使用电脑{self.continuous_usage_threshold // 60}分钟，请休息 {seconds // 60} 分钟{seconds % 60}秒！"
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("text").startswith("您已连续使用电脑"):
                widget.config(text=content)
                break

        self.root.after(1000, lambda: self.update_forced_rest_countdown(seconds - 1))

    def update_countdown(self, seconds):
        # ... (保持不变，原因同上) ...
        if not self.root or not self.root.winfo_exists() or not self.window_open:
            return

        if seconds <= 0:
            self.close_window()
            # 在主线程中调度关机
            self.main_root.after(0, self.execute_shutdown)
            return

        content = f"电脑将在 {seconds // 60} 分钟{seconds % 60}秒后自动关机\n请保存好您的工作！"
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("text").startswith("电脑将在"):
                widget.config(text=content)
                break

        self.root.after(1000, lambda: self.update_countdown(seconds - 1))

    def schedule_shutdown(self, minutes=5):
        # ... (保持不变) ...
        if self.shutdown_scheduled:
            return

        self.shutdown_scheduled = True
        self.shutdown_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)

        os.system(f"shutdown /s /t {minutes * 60}")
        self.logger.info(f"已计划在 {minutes} 分钟后关机")

        self.show_reminder_window(is_shutdown=True, countdown=minutes * 60)

    def cancel_shutdown(self):
        # ... (保持不变) ...
        if self.shutdown_scheduled:
            os.system("shutdown /a")
            self.shutdown_scheduled = False
            self.logger.info("已取消关机计划")

            # 关闭倒计时窗口
            self.close_window()

            # 显示取消提示 (通过主线程调度)
            self.main_root.after(0, self._show_cancel_message_on_main_thread)

    def _show_cancel_message_on_main_thread(self):
        """在主线程中显示取消关机提示"""
        # messagebox 是 Tkinter 的一部分，最好在主线程调用
        messagebox.showinfo("取消关机", "已取消自动关机计划。\n但请记得早点休息！", parent=self.main_root)
        self.logger.info("Cancel shutdown message shown.")

    def execute_shutdown(self):
        self.logger.info("执行自动关机")
        os.system("shutdown /s /t 0")

    def run(self):
        """运行休息提醒程序"""
        self.logger.info("休息提醒程序已启动")

        try:
            while True:
                is_evening, is_late_evening, is_forced_shutdown = self.check_time()

                if is_forced_shutdown:
                    self.logger.info("到达强制关机时间，执行关机")
                    # 直接调用系统关机，不需要通过 Tkinter 调度
                    self.execute_shutdown()
                    # 关机后程序会终止，不需要继续循环
                    break

                if self.usage_tracker:
                    continuous_usage_time = self.usage_tracker.get_continuous_usage_time()
                    if continuous_usage_time >= self.continuous_usage_threshold and not self.window_open:
                        self.logger.info(
                            f"连续使用{continuous_usage_time // 60}分钟，超过阈值{self.continuous_usage_threshold // 60}分钟，强制休息")
                        self.show_forced_rest_window(self.forced_rest_duration)

                if is_evening and not self.window_open:  # 只有当提醒窗口未打开时才显示
                    if is_late_evening and not self.shutdown_scheduled:
                        self.logger.info(
                            f"已过晚上 {self.shutdown_plan_hour}:{self.shutdown_plan_minute}，计划 {self.shutdown_delay_minutes} 分钟后关机")
                        self.schedule_shutdown(self.shutdown_delay_minutes)
                    elif not is_late_evening:  # 在计划关机时间之前，显示普通提醒
                        self.logger.info("显示休息提醒")
                        self.show_reminder_window()

                time.sleep(self.reminder_interval_seconds)

        except Exception as e:
            self.logger.error(f"程序运行出错: {str(e)}", exc_info=True)
        finally:
            if self.shutdown_scheduled:
                self.cancel_shutdown()
            self.close_window()  # 确保在线程结束时关闭所有打开的窗口