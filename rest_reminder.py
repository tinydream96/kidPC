import tkinter as tk
from tkinter import messagebox
import time
import datetime
import os
import threading
import sys
import logging
import configparser


class RestReminder:
    def __init__(self, usage_tracker=None):
        self.logger = self.setup_logger()
        self.shutdown_scheduled = False
        self.shutdown_time = None
        self.root = None
        self.usage_tracker = usage_tracker
        self.window_open = False  # 新增：跟踪窗口状态

        # 读取配置文件
        self.config = configparser.ConfigParser()
        if not os.path.exists('config.ini'):
            self.logger.error("config.ini not found!")
            raise FileNotFoundError("config.ini not found")

        try:
            self.config.read('config.ini')
            # 从配置文件获取参数
            self.evening_start_hour = self.config.getint('Settings', 'eveningStartHour', fallback=21)
            self.late_evening_start_hour = self.config.getint('Settings', 'lateEveningStartHour', fallback=21)
            self.late_evening_start_minute = self.config.getint('Settings', 'lateEveningStartMinute', fallback=30)
            self.shutdown_delay_minutes = self.config.getint('Settings', 'shutdownDelayMinutes', fallback=5)
            self.reminder_interval_seconds = self.config.getint('Settings', 'reminderIntervalSeconds', fallback=300)
            self.continuous_usage_threshold = self.config.getint('Settings', 'continuousUsageThreshold',
                                                                 fallback=45) * 60  # 默认为45分钟
            self.forced_rest_duration = self.config.getint('Settings', 'forcedRestDuration', fallback=5) * 60  # 默认为5分钟
        except Exception as e:
            self.logger.error(f"Error reading config.ini: {str(e)}")
            raise

    def setup_logger(self):
        """配置日志记录"""
        logger = logging.getLogger("RestReminder")
        logger.setLevel(logging.INFO)

        # 创建文件处理器
        file_handler = logging.FileHandler("rest_reminder.log")
        file_handler.setLevel(logging.INFO)

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 创建格式化器并添加到处理器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 将处理器添加到logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def check_time(self):
        """检查当前时间是否在晚上指定时间之后"""
        now = datetime.datetime.now()
        evening_start = now.replace(hour=self.evening_start_hour, minute=0, second=0, microsecond=0)
        late_evening_start = now.replace(hour=self.late_evening_start_hour, minute=self.late_evening_start_minute,
                                         second=0, microsecond=0)

        return now >= evening_start, now >= late_evening_start

    def show_reminder_window(self, is_shutdown=False, countdown=300):
        """显示提醒窗口"""
        if self.window_open:
            self.logger.info("窗口已打开，跳过显示")
            return

        self.window_open = True
        self.root = tk.Tk()
        self.root.title("休息提醒")
        self.root.attributes('-topmost', True)  # 窗口置顶
        self.root.geometry("600x400")  # 窗口大小
        self.root.configure(bg="#FF6B6B")  # 背景颜色

        # 设置字体
        title_font = ("微软雅黑", 36, "bold")
        content_font = ("微软雅黑", 24)

        # 创建标题
        title_label = tk.Label(
            self.root,
            text="该休息啦！",
            font=title_font,
            bg="#FF6B6B",
            fg="white"
        )
        title_label.pack(pady=40)

        # 创建内容
        if is_shutdown:
            content = f"电脑将在 {countdown // 60} 分钟后自动关机\n请保存好您的工作！"
        else:
            content = "已经很晚了，请注意休息！\n长时间使用电脑会影响健康。"

        content_label = tk.Label(
            self.root,
            text=content,
            font=content_font,
            bg="#FF6B6B",
            fg="white",
            wraplength=500
        )
        content_label.pack(pady=20)

        # 创建按钮
        button_frame = tk.Frame(self.root, bg="#FF6B6B")
        button_frame.pack(pady=30)

        if is_shutdown:
            # 关机倒计时窗口只显示取消按钮
            cancel_button = tk.Button(
                button_frame,
                text="取消关机",
                font=("微软雅黑", 18),
                bg="#FFD166",
                fg="#2A2A2A",
                width=15,
                command=self.cancel_shutdown
            )
            cancel_button.pack()
        else:
            # 普通提醒窗口显示知道了按钮
            ok_button = tk.Button(
                button_frame,
                text="知道了",
                font=("微软雅黑", 18),
                bg="#06D6A0",
                fg="white",
                width=15,
                command=self.close_window
            )
            ok_button.pack()

        # 窗口关闭协议
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

        # 如果是关机倒计时，启动倒计时更新
        if is_shutdown:
            self.update_countdown(countdown)

        self.root.mainloop()

    def show_forced_rest_window(self, countdown=300):
        """显示强制休息窗口"""
        if self.window_open:
            self.logger.info("窗口已打开，跳过显示")
            return

        self.window_open = True
        self.root = tk.Tk()
        self.root.title("强制休息提醒")

        # 全屏设置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")  # 全屏尺寸 + 坐标(左上角)

        self.root.attributes('-topmost', True)  # 窗口置顶
        self.root.configure(bg="#C2F0C2")  # 背景颜色

        # 禁止窗口大小调整
        self.root.resizable(width=False, height=False)
        # 👇 在这里加入 overrideredirect
        self.root.overrideredirect(True)  # 隐藏标题栏和窗口边框
        # 设置字体
        title_font = ("微软雅黑", int(screen_height / 10), "bold")
        content_font = ("微软雅黑", int(screen_height / 20))

        # 创建标题
        title_label = tk.Label(
            self.root,
            text="强制休息！",
            font=title_font,
            bg="#C2F0C2",
            fg="white"
        )
        title_label.pack(pady=int(screen_height * 0.1))

        # 创建内容
        content = f"您已连续使用电脑{self.continuous_usage_threshold // 60}分钟，请休息 {countdown // 60} 分钟！"
        content_label = tk.Label(
            self.root,
            text=content,
            font=content_font,
            bg="#C2F0C2",
            fg="white",
            wraplength=screen_width * 0.8
        )
        content_label.pack(pady=int(screen_height * 0.05))

        # 禁止关闭窗口
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        # 启动倒计时更新
        self.update_forced_rest_countdown(countdown)

        self.root.mainloop()

    def close_window(self):
        """安全关闭窗口"""
        if self.root and self.window_open:
            self.logger.info("关闭窗口")
            try:
                self.root.destroy()
            except Exception as e:
                self.logger.error(f"关闭窗口时出错: {e}")
            self.root = None
            self.window_open = False

    def update_forced_rest_countdown(self, seconds):
        """更新强制休息倒计时"""
        if not self.root or not self.window_open:
            return

        if seconds <= 0:
            self.close_window()
            if self.usage_tracker:
                self.usage_tracker.reset_continuous_usage_time()
            return

        # 更新标签文本
        content = f"您已连续使用电脑{self.continuous_usage_threshold // 60}分钟，请休息 {seconds // 60} 分钟{seconds % 60}秒！"
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("text").startswith("您已连续使用电脑"):
                widget.config(text=content)
                break

        # 1秒后再次更新
        self.root.after(1000, lambda: self.update_forced_rest_countdown(seconds - 1))

    def update_countdown(self, seconds):
        """更新关机倒计时"""
        if not self.root or not self.window_open:
            return

        if seconds <= 0:
            self.close_window()
            self.execute_shutdown()
            return

        # 更新标签文本
        content = f"电脑将在 {seconds // 60} 分钟{seconds % 60}秒后自动关机\n请保存好您的工作！"
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("text").startswith("电脑将在"):
                widget.config(text=content)
                break

        # 1秒后再次更新
        self.root.after(1000, lambda: self.update_countdown(seconds - 1))

    def schedule_shutdown(self, minutes=5):
        """计划电脑关机"""
        if self.shutdown_scheduled:
            return

        self.shutdown_scheduled = True
        self.shutdown_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)

        # 执行系统关机命令
        os.system(f"shutdown /s /t {minutes * 60}")
        self.logger.info(f"已计划在 {minutes} 分钟后关机")

        # 显示关机倒计时窗口
        self.show_reminder_window(is_shutdown=True, countdown=minutes * 60)

    def cancel_shutdown(self):
        """取消关机计划"""
        if self.shutdown_scheduled:
            os.system("shutdown /a")
            self.shutdown_scheduled = False
            self.logger.info("已取消关机计划")

            # 关闭倒计时窗口
            self.close_window()

            # 显示取消提示
            self.show_cancel_message()

    def show_cancel_message(self):
        """显示取消关机提示"""
        if self.window_open:
            return

        self.window_open = True
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showinfo("取消关机", "已取消自动关机计划。\n但请记得早点休息！")
        root.destroy()
        self.window_open = False

    def execute_shutdown(self):
        """执行关机命令"""
        self.logger.info("执行自动关机")
        os.system("shutdown /s /t 0")

    def run(self):
        """运行休息提醒程序"""
        self.logger.info("休息提醒程序已启动")

        try:
            while True:
                is_evening, is_late_evening = self.check_time()

                # 检查连续使用时间
                if self.usage_tracker:
                    continuous_usage_time = self.usage_tracker.get_continuous_usage_time()
                    if continuous_usage_time >= self.continuous_usage_threshold:
                        # 连续使用时间超过阈值，强制休息
                        self.logger.info(
                            f"连续使用{continuous_usage_time // 60}分钟，超过阈值{self.continuous_usage_threshold // 60}分钟，强制休息")
                        self.show_forced_rest_window(self.forced_rest_duration)

                if is_evening:
                    if is_late_evening and not self.shutdown_scheduled:
                        # 晚上指定时间后，计划指定分钟后关机
                        self.logger.info(
                            f"已过晚上 {self.late_evening_start_hour}:{self.late_evening_start_minute}，计划 {self.shutdown_delay_minutes} 分钟后关机")
                        self.schedule_shutdown(self.shutdown_delay_minutes)
                    else:
                        # 晚上指定时间前，每指定间隔提醒一次
                        self.logger.info("显示休息提醒")
                        self.show_reminder_window()

                # 等待指定间隔
                time.sleep(self.reminder_interval_seconds)

        except KeyboardInterrupt:
            self.logger.info("程序被用户中断")
        except Exception as e:
            self.logger.error(f"程序运行出错: {str(e)}", exc_info=True)
        finally:
            # 如果有关机计划，取消它
            if self.shutdown_scheduled:
                self.cancel_shutdown()

            # 确保窗口被关闭
            self.close_window()