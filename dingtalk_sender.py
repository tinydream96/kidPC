# -*- coding: utf-8 -*-

import os
import time
import socket
import platform
import requests
import threading
import logging
from PIL import ImageGrab
from datetime import datetime
from typing import Optional


class DingTalkSender:
    """
    钉钉图片发送器 - 定期发送桌面截图到钉钉群
    """

    def __init__(self, config_manager, usage_tracker=None):
        """
        初始化钉钉发送器

        Args:
            config_manager: 配置管理器实例
            usage_tracker: 使用时间追踪器实例（可选）
        """
        self.config_manager = config_manager
        self.usage_tracker = usage_tracker
        self.logger = logging.getLogger("DingTalkSender")
        self.running = False
        self.thread = None

        # 从配置文件读取参数
        self.webhook_url = self.config_manager.get_setting('Settings', 'dingtalkwebhook', fallback='')
        self.imgbb_api_key = self.config_manager.get_setting('Settings', 'imgbbapi', fallback='')
        self.interval_minutes = self.config_manager.get_setting('Settings', 'dingtalkinterval', type=int, fallback=5)

        # API URLs
        self.imgbb_upload_url = "https://api.imgbb.com/1/upload"

        # 临时文件名
        self.screenshot_filename = "dingtalk_screenshot_temp.png"

        self.logger.info("DingTalkSender initialized")

    def get_system_info(self) -> dict:
        """
        获取系统信息

        Returns:
            包含系统信息的字典
        """
        try:
            # --- IP地址获取方式修改 ---
            # 通过连接外部服务器获取IP地址，更准确
            ip_address = "未知"
            s = None  # 初始化s
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]
            except Exception as e:
                self.logger.warning(f"获取IP地址失败，将尝试备用方法: {e}")
                try:
                    ip_address = socket.gethostbyname(socket.gethostname())
                except Exception as e_inner:
                    self.logger.error(f"备用IP获取方法也失败了: {e_inner}")
                    ip_address = "127.0.0.1"  # 最后的备用方案
            finally:
                if s:
                    s.close()
            # --- 修改结束 ---

            # 获取电脑名称
            computer_name = platform.node()

            # 获取使用时间
            usage_time = "未知"
            if self.usage_tracker:
                today_usage_seconds = self.usage_tracker.get_usage_time()
                usage_time = self.usage_tracker.format_time(today_usage_seconds)

            # 获取当前时间
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return {
                'ip': ip_address,  # 使用新的ip_address变量
                'computer_name': computer_name,
                'usage_time': usage_time,
                'current_time': current_time,
                'hostname': computer_name  # hostname和computer_name通常一样
            }
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return {
                'ip': '未知',
                'computer_name': '未知',
                'usage_time': '未知',
                'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'hostname': '未知'
            }

    def take_screenshot(self) -> bool:
        """
        截取屏幕并保存

        Returns:
            成功返回True，失败返回False
        """
        try:
            screenshot = ImageGrab.grab()
            screenshot.save(self.screenshot_filename)
            self.logger.debug(f"截图已保存: {self.screenshot_filename}")
            return True
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            return False

    def upload_to_imgbb(self, file_path: str) -> Optional[str]:
        """
        上传图片到ImgBB图床

        Args:
            file_path: 图片文件路径

        Returns:
            成功返回图片URL，失败返回None
        """
        if not self.imgbb_api_key:
            self.logger.error("ImgBB API Key未配置")
            return None

        try:
            with open(file_path, 'rb') as f:
                params = {'key': self.imgbb_api_key}
                files = {'image': f}
                response = requests.post(self.imgbb_upload_url, params=params, files=files, timeout=60)
                response.raise_for_status()

                data = response.json()
                if data.get("success") and data.get("data"):
                    image_url = data['data']['url']
                    self.logger.debug(f"图片上传成功: {image_url}")
                    return image_url
                else:
                    error_message = data.get("error", {}).get("message", "未知错误")
                    self.logger.error(f"图片上传失败: {error_message}")
                    return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"上传图片网络错误: {e}")
            return None
        except Exception as e:
            self.logger.error(f"上传图片时发生错误: {e}")
            return None

    def send_webhook_message(self, image_url: str, system_info: dict) -> bool:
        """
        通过Webhook发送消息到钉钉

        Args:
            image_url: 图片URL
            system_info: 系统信息字典

        Returns:
            成功返回True，失败返回False
        """
        if not self.webhook_url:
            self.logger.error("钉钉Webhook URL未配置")
            return False

        try:
            headers = {'Content-Type': 'application/json'}

            # 构建消息内容
            message_text = f"""#### 电脑监控截图
**🖥️ 电脑名称:** {system_info['computer_name']}\n
**🌐 IP地址:** {system_info['ip']}\n
**⏰ 当前时间:** {system_info['current_time']}\n
**📊 今日使用时间:** {system_info['usage_time']}\n

![桌面截图]({image_url})"""

            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "电脑监控截图",
                    "text": message_text
                }
            }

            response = requests.post(self.webhook_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data.get("errcode") == 0:
                self.logger.info("钉钉消息发送成功")
                return True
            else:
                self.logger.error(f"钉钉消息发送失败: {data.get('errmsg')}")
                return False

        except requests.exceptions.RequestException as e:
            self.logger.error(f"发送钉钉消息网络错误: {e}")
            return False
        except Exception as e:
            self.logger.error(f"发送钉钉消息时发生错误: {e}")
            return False

    def send_screenshot(self) -> bool:
        """
        发送截图到钉钉

        Returns:
            成功返回True，失败返回False
        """
        try:
            # 1. 截取屏幕
            if not self.take_screenshot():
                return False

            # 2. 获取系统信息
            system_info = self.get_system_info()

            # 3. 通过Webhook方式发送
            if self.webhook_url and self.imgbb_api_key:
                self.logger.debug("使用Webhook方式发送")
                image_url = self.upload_to_imgbb(self.screenshot_filename)
                if image_url:
                    success = self.send_webhook_message(image_url, system_info)
                    if success:
                        return True
            else:
                self.logger.error("钉钉Webhook URL或ImgBB API Key未配置")

            self.logger.error("钉钉发送失败")
            return False

        except Exception as e:
            self.logger.error(f"发送截图时发生错误: {e}")
            return False
        finally:
            # 清理临时文件
            if os.path.exists(self.screenshot_filename):
                try:
                    os.remove(self.screenshot_filename)
                    self.logger.debug("临时截图文件已清理")
                except Exception as e:
                    self.logger.warning(f"清理临时文件失败: {e}")

    def run(self):
        """
        运行钉钉发送器主循环
        """
        self.running = True
        self.logger.info(f"钉钉发送器开始运行，发送间隔: {self.interval_minutes}分钟")

        try:
            while self.running:
                try:
                    # 发送截图
                    self.send_screenshot()

                    # 等待指定间隔
                    for _ in range(self.interval_minutes * 60):  # 转换为秒
                        if not self.running:
                            break
                        time.sleep(1)

                except Exception as e:
                    self.logger.error(f"发送循环中发生错误: {e}")
                    # 发生错误时等待一段时间再继续
                    time.sleep(60)

        except Exception as e:
            self.logger.critical(f"钉钉发送器运行时发生严重错误: {e}")
        finally:
            self.logger.info("钉钉发送器已停止")

    def start(self):
        """
        启动钉钉发送器线程
        """
        if not self.running:
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            self.logger.info("钉钉发送器线程已启动")

    def stop(self):
        """
        停止钉钉发送器
        """
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        self.logger.info("钉钉发送器已停止")