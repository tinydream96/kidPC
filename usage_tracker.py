from config_manager import ConfigManager
import os
import time
# import configparser # 移除，使用 ConfigManager
import json
import datetime
import logging
import threading
from typing import Optional


class UsageTracker:
    logger: logging.Logger
    running: bool
    config_manager: ConfigManager
    data_folder: str
    usage_stats_file: str
    continuous_usage_threshold: int
    daily_usage_time: float
    last_check_time: float
    lock: threading.Lock
    continuous_usage_time: float

    def __init__(self, config_manager: ConfigManager) -> None:
        self.logger = logging.getLogger("UsageTracker")
        self.running = False
        self.config_manager = config_manager

        # 从 ConfigManager 获取参数
        # Note: get_setting can return None if fallback is None, ensure appropriate handling or default
        data_folder_setting = self.config_manager.get_setting('Settings', 'dataFolder')
        self.data_folder = str(data_folder_setting) if data_folder_setting is not None else ".\\default_data" # Ensure str

        usage_stats_file_setting = self.config_manager.get_setting(
            'Settings', 'usageStatsFile',
            fallback=os.path.join(self.data_folder, 'usage_stats.json')
        )
        self.usage_stats_file = str(usage_stats_file_setting) if usage_stats_file_setting is not None else os.path.join(self.data_folder, 'usage_stats.json')


        continuous_usage_threshold_setting = self.config_manager.get_setting(
            'Settings', 'continuousUsageThreshold', type=int, fallback=600
        )
        self.continuous_usage_threshold = int(continuous_usage_threshold_setting) if continuous_usage_threshold_setting is not None else 600


        self.daily_usage_time = 0.0
        self.last_check_time = time.time()
        self.lock = threading.Lock()
        self.continuous_usage_time = 0.0

        os.makedirs(self.data_folder, exist_ok=True)
        self.logger.info(f"Data folder '{self.data_folder}' ensured to exist.")

        self.load_usage_stats()

    def load_usage_stats(self) -> float:
        """从文件加载上次保存的使用统计，并根据日期判断是否重置"""
        today_date = datetime.date.today().isoformat()
        if os.path.exists(self.usage_stats_file):
            try:
                with open(self.usage_stats_file, 'r') as f:
                    stats = json.load(f)

                if stats.get('today_date') == today_date:  # 使用 'today_date' 而不是 'date'
                    self.daily_usage_time = stats.get('daily_usage_time', 0)
                    self.logger.info(
                        f"Loaded daily usage time from '{self.usage_stats_file}' for today: {self.format_time(self.daily_usage_time)}")
                else:
                    self.daily_usage_time = 0
                    self.logger.info("New day detected. Daily usage time reset to 0.")

                self.continuous_usage_time = 0
                self.last_check_time = time.time()

            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding JSON from usage stats file: {e}. Resetting stats.")
                self.daily_usage_time = 0
                self.continuous_usage_time = 0
            except Exception as e:
                self.logger.error(f"Error loading usage stats: {e}. Resetting stats.")
                self.daily_usage_time = 0
                self.continuous_usage_time = 0
        else:
            self.logger.info("Usage stats file not found. Daily usage time initialized to 0.")
        self.daily_usage_time = 0.0
        self.continuous_usage_time = 0.0

        return self.daily_usage_time

    def save_usage_stats(self) -> None:
        """保存当前的使用统计到文件"""
        with self.lock:
            today_date = datetime.date.today().isoformat()
            stats = {
                'today_date': today_date,
                'daily_usage_time': self.daily_usage_time
            }
            try:
                with open(self.usage_stats_file, 'w') as f:
                    json.dump(stats, f)
                self.logger.info(
                    f"Saved daily usage time to '{self.usage_stats_file}': {self.format_time(self.daily_usage_time)}")
            except Exception as e:
                self.logger.error(f"Error saving usage stats: {e}")

    def update_usage_time(self) -> None:
        """更新累计使用时间和连续使用时间"""
        with self.lock:
            current_time = time.time()
            time_elapsed = current_time - self.last_check_time
            self.last_check_time = current_time
            self.daily_usage_time += time_elapsed
            self.continuous_usage_time += time_elapsed
            self.logger.debug(
                f"Added {time_elapsed:.2f} seconds of usage time. Total: {self.format_time(self.daily_usage_time)}, Continuous: {self.format_time(self.continuous_usage_time)}")

    def get_usage_time(self) -> float:
        """获取当前累计使用时间"""
        with self.lock:
            return self.daily_usage_time

    def get_continuous_usage_time(self) -> float:
        """获取当前连续使用时间"""
        with self.lock:
            return self.continuous_usage_time

    def reset_continuous_usage_time(self) -> None:
        """重置连续使用时间"""
        with self.lock:
            self.continuous_usage_time = 0.0

    def start_tracking(self) -> None:
        """开始跟踪电脑使用时间"""
        self.running = True
        self.logger.info("Started tracking computer usage time")

        try:
            while self.running:
                self.update_usage_time()
                time.sleep(1)
        except Exception as e:
            self.logger.critical(f"Error in tracking thread: {str(e)}")
        finally:
            self.save_usage_stats()
            self.logger.info("UsageTracker thread stopped.")

    def stop_tracking(self) -> None:
        self.running = False
        self.logger.info("Stopping tracking computer usage time.")

    def format_time(self, seconds: float) -> str:
        """将秒数格式化为HH:MM:SS格式"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"