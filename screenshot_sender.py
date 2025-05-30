from config_manager import ConfigManager
from usage_tracker import UsageTracker
from typing import Optional, Dict
import os
import time
# import configparser # 移除，使用 ConfigManager
import requests
from PIL import ImageGrab
import logging
import socket
import datetime  # 确保导入 datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class ScreenshotSender:
    logger: logging.Logger
    usage_tracker: Optional[UsageTracker]
    running: bool
    config_manager: ConfigManager
    data_folder: str
    bot_token: str
    chat_id: str
    proxy: Optional[str]
    interval: int
    proxies: Optional[Dict[str, str]]

    def __init__(self, config_manager: ConfigManager, usage_tracker: Optional[UsageTracker] = None) -> None:
        self.logger = logging.getLogger("ScreenshotSender")
        self.usage_tracker = usage_tracker
        self.running = False

        self.config_manager = config_manager

        # 从 ConfigManager 获取参数, ensuring types
        data_folder_setting = self.config_manager.get_setting('Settings', 'dataFolder')
        self.data_folder = str(data_folder_setting) if data_folder_setting is not None else ".\\default_screenshots"

        bot_token_setting = self.config_manager.get_setting('Settings', 'botToken')
        self.bot_token = str(bot_token_setting) if bot_token_setting is not None else "YOUR_BOT_TOKEN"

        chat_id_setting = self.config_manager.get_setting('Settings', 'chatId')
        self.chat_id = str(chat_id_setting) if chat_id_setting is not None else "YOUR_CHAT_ID"

        proxy_setting = self.config_manager.get_setting('Settings', 'proxy', fallback='')
        self.proxy = str(proxy_setting) if proxy_setting else None # Ensure it's None if empty string

        interval_setting = self.config_manager.get_setting('Settings', 'screenshotInterval', type=int, fallback=1)
        self.interval = int(interval_setting) * 60 if interval_setting is not None else 60 # Ensure int, convert to seconds

        # 配置代理
        if self.proxy:
            self.proxies = {'http': self.proxy, 'https': self.proxy}
            self.logger.info(f"Using proxy: {self.proxy}")
        else:
            self.proxies = None
            self.logger.info("No proxy configured.")

        # 确保数据文件夹存在
        os.makedirs(self.data_folder, exist_ok=True)
        self.logger.info(f"Data folder '{self.data_folder}' ensured to exist for screenshots.")

    def take_screenshot(self) -> Optional[str]:
        """截取全屏并保存"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.data_folder, f"screenshot_{timestamp}.png")

            # 兼容多显示器
            screenshot = ImageGrab.grab(all_screens=True)
            screenshot.save(filename)
            self.logger.info(f"Screenshot saved to {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            return None

    def send_screenshot(self, usage_time_seconds: float) -> bool:
        """发送截图到 Telegram"""
        filepath = self.take_screenshot()
        if not filepath:
            return False

        if not os.path.exists(filepath):
            self.logger.error("Screenshot file does not exist for sending.")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"

            ip_address = "Unknown IP"
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]
            except Exception:
                ip_address = "127.0.0.1"
            finally:
                s.close()

            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            usage_time_formatted = self.usage_tracker.format_time(usage_time_seconds) if self.usage_tracker else "N/A"

            caption = (
                f"IP地址: {ip_address}\n"
                f"截图时间: {current_time}\n"
                f"今日累计使用: {usage_time_formatted}"
            )

            with open(filepath, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': self.chat_id, 'caption': caption}

                for attempt in range(3):
                    try:
                        response = requests.post(url, files=files, data=data,
                                                 proxies=self.proxies, verify=False, timeout=60)
                        response.raise_for_status()
                        self.logger.info("Photo sent successfully")
                        if self.usage_tracker:
                            self.usage_tracker.save_usage_stats()
                            self.logger.info("Usage stats saved after sending screenshot")
                        break
                    except requests.exceptions.RequestException as e:
                        self.logger.warning(f"Send attempt {attempt + 1} failed: {str(e)}")
                        if attempt == 2:
                            self.logger.error("Max retries reached, giving up on sending screenshot")
                            return False
                else:
                    return False

        except Exception as e:
            self.logger.error(f"Error sending screenshot: {str(e)}")
            return False
        finally:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    self.logger.info(f"Screenshot file {filepath} deleted.")
                except Exception as e:
                    self.logger.error(f"Error deleting screenshot file {filepath}: {e}")
        return True

    def run(self) -> None:
        """线程运行方法，持续发送截图"""
        self.running = True
        self.logger.info("ScreenshotSender thread started.")
        try:
            while self.running:
                usage_time = self.usage_tracker.get_usage_time() if self.usage_tracker else 0
                self.send_screenshot(usage_time)
                time.sleep(self.interval)
        except Exception as e:
            self.logger.critical(f"ScreenshotSender thread encountered a critical error: {e}", exc_info=True)
        finally:
            self.running = False
            self.logger.info("ScreenshotSender thread fully exited.")

    def stop(self) -> None:
        """停止截图发送线程"""
        self.running = False
        self.logger.info("ScreenshotSender stopping.")