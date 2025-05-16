# main.py

import time
import threading
import logging
import configparser
from screenshot_sender import ScreenshotSender
from usage_tracker import UsageTracker
from float_window import FloatWindow
from rest_reminder import RestReminder
from update_checker import check_and_update_files

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='screenshot_bot.log'
)

# 读取配置文件
config = configparser.ConfigParser()
if not os.path.exists('config.ini'):
    logging.error("config.ini not found!")
    raise FileNotFoundError("config.ini not found")
try:
    config.read('config.ini')
    proxy = config.get('Settings', 'proxy', fallback='')
    repo_owner = config.get('Settings', 'repo_owner')
    repo_name = config.get('Settings', 'repo_name')
    branch = 'main'
except Exception as e:
    logging.error(f"Error reading config.ini: {str(e)}")
    raise

# 检查并更新文件
check_and_update_files(repo_owner, repo_name, branch, proxy)

# 初始化组件
tracker = UsageTracker()
sender = ScreenshotSender(usage_tracker=tracker)  # 传递UsageTracker实例
float_window = FloatWindow(tracker)
reminder = RestReminder(usage_tracker=tracker)  # 传递UsageTracker实例

logging.info("Screenshot bot started")

try:
    # 启动时间统计线程
    tracker_thread = threading.Thread(target=tracker.start_tracking, daemon=True)
    tracker_thread.start()

    # 启动浮窗线程
    if sender.show_float_window:
        window_thread = threading.Thread(target=float_window.run, daemon=True)
        window_thread.start()

    # 启动休息提醒线程
    reminder_thread = threading.Thread(target=reminder.run, daemon=True)
    reminder_thread.start()

    # 主循环处理截图发送
    while True:
        # 发送截图
        usage_time = tracker.get_usage_time()
        sender.send_screenshot(usage_time)

        # 等待下一个间隔
        time.sleep(sender.interval)

except KeyboardInterrupt:
    # 程序退出前保存使用数据
    tracker.save_usage_stats()
    logging.info("Bot stopped by user")
except Exception as e:
    # 发生异常时也保存使用数据
    tracker.save_usage_stats()
    logging.critical(f"Unexpected error: {str(e)}", exc_info=True)