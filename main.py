import tkinter as tk
import time
import threading
import logging
from screenshot_sender import ScreenshotSender
from usage_tracker import UsageTracker
from float_window import FloatWindow
from rest_reminder import RestReminder
from config_manager import ConfigManager # 确保导入 ConfigManager
from config_ui import ConfigUI # 确保导入 ConfigUI

# 配置日志
logging.basicConfig(
    level=logging.DEBUG, # 调试时改为 DEBUG，生产环境建议 INFO
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='screenshot_bot.log',
    filemode='a'
)

logging.info("Starting Screenshot Bot application.")

# 创建主 Tkinter 根窗口并隐藏
root = tk.Tk()
root.withdraw() # 隐藏主窗口
root.title("Kid PC Monitor (Hidden)") # 避免无标题窗口警告

# 初始化配置管理器
config_manager = ConfigManager()
logging.info("Loaded configuration from config.ini")

# 初始化组件，并传递必要的实例
# 所有组件都应接收 main_root 和 config_manager
tracker = UsageTracker(config_manager) # 传递 ConfigManager
# 加载今日使用时间
today_usage_time_seconds = tracker.load_usage_stats()
logging.info(f"Loaded today's usage time: {tracker.format_time(today_usage_time_seconds)}")

sender = ScreenshotSender(config_manager, usage_tracker=tracker) # 传递 ConfigManager
float_window = FloatWindow(root, tracker) # 传递主根窗口
reminder = RestReminder(root, config_manager, usage_tracker=tracker) # 传递主根窗口和 ConfigManager

# 初始化配置 UI
# ConfigUI 实例必须在 main.py 中创建
config_ui = ConfigUI(root, config_manager) # 传递主根窗口和 ConfigManager
logging.info("All UI components and managers initialized.")
logging.info("Tray icon created (by ConfigUI).") # ConfigUI 内部会创建并启动托盘图标线程

try:
    # 启动时间统计线程
    tracker_thread = threading.Thread(target=tracker.start_tracking, daemon=True)
    tracker_thread.start()
    logging.info("UsageTracker thread started.")

    # 启动浮窗线程
    if config_manager.get_setting('Settings', 'showFloatWindow', type=bool, fallback=True):
        window_thread = threading.Thread(target=float_window.run, daemon=True)
        window_thread.start()
        logging.info("FloatWindow thread started.")
    else:
        logging.info("Float window is disabled in config.")

    # 启动休息提醒线程
    if config_manager.get_setting('Settings', 'enableRestReminder', type=bool, fallback=True):
        reminder_thread = threading.Thread(target=reminder.run, daemon=True)
        reminder_thread.start()
        logging.info("RestReminder thread started.")
    else:
        logging.info("Rest reminder is disabled in config.")

    # 启动截图发送线程
    # sender.run() 方法现在包含了循环逻辑
    screenshot_sender_thread = threading.Thread(target=sender.run, daemon=True)
    screenshot_sender_thread.start()
    logging.info("Screenshot sender thread started.")

    # 运行 Tkinter 主循环
    # 这一行必须是主线程的最后一步，它会保持程序运行，处理所有UI事件
    logging.info("Starting Tkinter main loop.")
    root.mainloop() # 阻塞主线程，等待UI事件

except KeyboardInterrupt:
    logging.info("Application interrupted by user.")
except Exception as e:
    logging.critical(f"An unexpected error occurred: {e}", exc_info=True)
finally:
    logging.info("Application shutting down.")
    # 在这里添加清理代码，确保所有线程停止和数据保存
    tracker.stop_tracking() # 确保tracker停止并保存数据
    float_window.stop() # 确保浮窗线程停止
    # reminder 线程和 sender 线程的停止已在其 run() 方法的 finally 块中处理，
    # 或者通过 self.running 标志位在外部控制。
    # 对于守护线程，当主程序退出时它们会自动终止，但显式停止会更好。
    # 鉴于 mainloop 退出后程序可能很快终止，这些 stop() 调用有时可能无法完全执行。
    # 但在 try-finally 块中放置，是为了尽可能地进行清理。