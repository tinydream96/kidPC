# main.py
import time
import threading
import logging
from screenshot_sender import ScreenshotSender
from usage_tracker import UsageTracker
from float_window import FloatWindow
from rest_reminder import RestReminder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='screenshot_bot.log'
)
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