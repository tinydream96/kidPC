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
    def __init__(self):
        self.logger = self.setup_logger()
        self.shutdown_scheduled = False
        self.shutdown_time = None
        self.root = None
        # 读取配置文件
        self.config = configparser.ConfigParser()
        if not os.path.exists('config.ini'):
            self.logger.error("config.ini not found!")
            raise FileNotFoundError("config.ini not found")
        try:
            self.config.read('config.ini')
            # 从配置文件获取参数
            self.reminder_start_hour = self.config.getint('Settings', 'reminderStartHour')
            self.reminder_interval_minutes = self.config.getint('Settings', 'reminderIntervalMinutes')
            self.shutdown_start_hour = self.config.getint('Settings', 'shutdownStartHour')
            self.shutdown_start_minute = self.config.getint('Settings', 'shutdownStartMinute')
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
        """检查当前时间是否在指定时间之后"""
        now = datetime.datetime.now()
        evening_start = now.replace(hour=self.reminder_start_hour, minute=0, second=0, microsecond=0)
        shutdown_start = now.replace(hour=self.shutdown_start_hour, minute=self.shutdown_start_minute, second=0, microsecond=0)

        return now >= evening_start, now >= shutdown_start

    def show_reminder_window(self, is_shutdown=False, countdown=300):
        """显示提醒窗口"""
        if self.root and not self.root.winfo_exists():
            self.root = None

        if not self.root:
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
                    command=self.root.destroy
                )
                ok_button.pack()

            # 窗口关闭协议
            self.root.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁止关闭窗口

            # 如果是关机倒计时，启动倒计时更新
            if is_shutdown:
                self.update_countdown(countdown)

            self.root.mainloop()

    def update_countdown(self, seconds):
        """更新关机倒计时"""
        if seconds <= 0:
            self.root.destroy()
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
            if self.root:
                self.root.destroy()
                self.root = None

            # 显示取消提示
            self.show_cancel_message()

    def show_cancel_message(self):
        """显示取消关机提示"""
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showinfo("取消关机", "已取消自动关机计划。\n但请记得早点休息！")
        root.destroy()

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

                if is_evening:
                    if is_late_evening and not self.shutdown_scheduled:
                        # 到达指定关机时间，计划5分钟后关机
                        self.logger.info("已过指定关机时间，计划5分钟后关机")
                        self.schedule_shutdown(5)
                    else:
                        # 到达指定提醒时间后，每隔指定分钟提醒一次
                        self.logger.info("显示休息提醒")
                        self.show_reminder_window()

                # 等待指定分钟
                time.sleep(self.reminder_interval_minutes * 60)

        except KeyboardInterrupt:
            self.logger.info("程序被用户中断")
        except Exception as e:
            self.logger.error(f"程序运行出错: {str(e)}", exc_info=True)
        finally:
            # 如果有关机计划，取消它
            if self.shutdown_scheduled:
                self.cancel_shutdown()


if __name__ == "__main__":
    reminder = RestReminder()

    # 在单独的线程中运行，避免阻塞主线程
    thread = threading.Thread(target=reminder.run)
    thread.daemon = True
    thread.start()

    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)