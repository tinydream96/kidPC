import configparser
import os
import time
import json
import datetime
import logging
import threading


class UsageTracker:
    def __init__(self):
        self.logger = logging.getLogger("UsageTracker")
        self.running = False

        # 读取配置文件
        self.config = configparser.ConfigParser()
        if not os.path.exists('config.ini'):
            self.logger.error("config.ini not found!")
            raise FileNotFoundError("config.ini not found")

        try:
            self.config.read('config.ini')
            # 从配置文件获取参数
            self.data_folder = self.config.get('Settings', 'dataFolder')
            self.usage_stats_file = self.config.get('Settings', 'usageStatsFile',
                                                    fallback=os.path.join(self.data_folder, 'usage_stats.json'))
        except Exception as e:
            self.logger.error(f"Error reading config.ini: {str(e)}")
            raise

        # 使用时间统计相关变量
        self.daily_usage_time = 0  # 当天累计使用时间（秒）
        self.last_check_time = time.time()  # 上次检查时间
        self.lock = threading.Lock()  # 线程锁

        # 确保数据文件夹存在
        os.makedirs(self.data_folder, exist_ok=True)

        # 加载历史使用数据
        self.load_usage_stats()

    def load_usage_stats(self):
        """从文件加载历史使用数据"""
        if os.path.exists(self.usage_stats_file):
            try:
                with open(self.usage_stats_file, 'r') as f:
                    stats = json.load(f)
                    today = datetime.date.today().isoformat()

                    # 如果有今天的数据，加载使用时间
                    if 'date' in stats and stats['date'] == today:
                        self.daily_usage_time = stats.get('usage_time', 0)
                        self.logger.info(f"Loaded today's usage time: {self.format_time(self.daily_usage_time)}")
                    else:
                        # 不是今天的数据，重置统计
                        self.logger.info("Resetting usage stats: different date or invalid file")
                        self.daily_usage_time = 0  # 直接设置类属性
                        self.save_usage_stats()  # 正确调用：不需要参数
            except Exception as e:
                self.logger.error(f"Error loading usage stats: {str(e)}")
                self.daily_usage_time = 0
                self.save_usage_stats()  # 正确调用
        else:
            # 文件不存在，创建新的统计
            self.logger.info("Creating new usage stats file")
            self.daily_usage_time = 0
            self.save_usage_stats()  # 正确调用

    def save_usage_stats(self):
        """保存使用数据到文件"""
        today = datetime.date.today().isoformat()
        stats = {
            'date': today,
            'usage_time': self.daily_usage_time
        }

        try:
            with open(self.usage_stats_file, 'w') as f:
                json.dump(stats, f)
            self.logger.info(f"Saved usage stats: {self.daily_usage_time} seconds for {today}")
        except Exception as e:
            self.logger.error(f"Error saving usage stats: {str(e)}")

    def format_time(self, seconds):
        """将秒数格式化为HH:MM:SS格式"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def update_usage_time(self):
        """更新使用时间（不考虑系统闲置）"""
        current_time = time.time()

        # 检查是否需要重置日期（跨天）
        today = datetime.date.today().isoformat()
        if os.path.exists(self.usage_stats_file):
            try:
                with open(self.usage_stats_file, 'r') as f:
                    stats = json.load(f)
                    if 'date' not in stats or stats['date'] != today:
                        self.logger.info("New day detected. Resetting usage stats.")
                        self.daily_usage_time = 0
                        self.save_usage_stats()
            except Exception as e:
                self.logger.error(f"Error checking date: {str(e)}")

        # 更新使用时间
        with self.lock:
            time_elapsed = current_time - self.last_check_time
            self.last_check_time = current_time
            self.daily_usage_time += time_elapsed
            self.logger.debug(
                f"Added {time_elapsed:.2f} seconds of usage time. Total: {self.format_time(self.daily_usage_time)}")

    def get_usage_time(self):
        """获取当前累计使用时间"""
        with self.lock:
            return self.daily_usage_time

    def start_tracking(self):
        """开始跟踪电脑使用时间"""
        self.running = True
        self.logger.info("Started tracking computer usage time")

        try:
            while self.running:
                self.update_usage_time()
                time.sleep(1)  # 每秒检查一次
        except Exception as e:
            self.logger.critical(f"Error in tracking thread: {str(e)}")
        finally:
            # 确保退出前保存数据
            self.save_usage_stats()

    def stop_tracking(self):
        """停止跟踪电脑使用时间"""
        self.running = False
        self.save_usage_stats()
        self.logger.info("Stopped tracking computer usage time")