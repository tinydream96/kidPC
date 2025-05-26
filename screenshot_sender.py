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
    def __init__(self, config_manager, usage_tracker=None):  # 接收 ConfigManager 实例
        self.logger = logging.getLogger("ScreenshotSender")
        self.usage_tracker = usage_tracker
        self.running = False  # 控制线程运行状态

        self.config_manager = config_manager  # 存储 ConfigManager 实例

        # 从 ConfigManager 获取参数
        self.data_folder = self.config_manager.get_setting('Settings', 'dataFolder')
        self.bot_token = self.config_manager.get_setting('Settings', 'botToken')
        self.chat_id = self.config_manager.get_setting('Settings', 'chatId')
        self.proxy = self.config_manager.get_setting('Settings', 'proxy', fallback='')
        self.interval = self.config_manager.get_setting('Settings', 'screenshotInterval', type=int,
                                                        fallback=1) * 60  # 转换为秒
        # self.show_float_window = self.config_manager.get_setting('Settings', 'showFloatWindow', type=bool, fallback=True) # 这个设置在 ScreenshotSender 中不直接使用，可以移除

        # 配置代理
        self.proxies = {
            'http': self.proxy,
            'https': self.proxy
        } if self.proxy else None

        if self.proxies:
            self.logger.info(f"Using proxy: {self.proxy}")
        else:
            self.logger.info("No proxy configured.")

        # 确保数据文件夹存在
        os.makedirs(self.data_folder, exist_ok=True)
        self.logger.info(f"Data folder '{self.data_folder}' ensured to exist for screenshots.")

    def take_screenshot(self):
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

    def send_screenshot(self, usage_time_seconds):
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

    def run(self):
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

    def stop(self):
        """停止截图发送线程"""
        self.running = False
        self.logger.info("ScreenshotSender stopping.")