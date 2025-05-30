import configparser
import os
import logging
from typing import Optional, Union, Dict, List, Any, Type

class ConfigManager:
    CONFIG_FILE: str = 'config.ini'
    logger: logging.Logger
    config: configparser.ConfigParser

    def __init__(self) -> None:
        self.logger = logging.getLogger("ConfigManager")
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self) -> None:
        if not os.path.exists(self.CONFIG_FILE):
            self.logger.warning(f"Configuration file '{self.CONFIG_FILE}' not found. Creating with default settings.")
            self._create_default_config()
        # 确保以 utf-8 编码读取，防止中文乱码
        self.config.read(self.CONFIG_FILE, encoding='utf-8')
        self.logger.info(f"Configuration loaded from {self.CONFIG_FILE}")

    def _create_default_config(self) -> None:
        # 定义默认设置
        self.config['Settings'] = {
            'dataFolder': '.\\screenshots',
            'botToken': 'YOUR_BOT_TOKEN', # 请替换为您的 Telegram Bot Token
            'chatId': 'YOUR_CHAT_ID',     # 请替换为您的 Telegram Chat ID
            'proxy': '', # 例如: '192.168.100.101:1081'，如果不需要代理，留空即可
            'screenshotInterval': '1', # 截图间隔（分钟）
            'usageStatsFile': '.\\usage_stats.json',
            'showFloatWindow': 'true', # 是否显示浮动窗口 (true/false)
            'enableRestReminder': 'true', # 是否启用休息提醒 (true/false)
            'firstReminderHour': '21', # 首次提醒时间（小时，24小时制）
            'shutdownPlanHour': '21', # 计划关机时间（小时）
            'shutdownPlanMinute': '30', # 计划关机时间（分钟）
            'shutdownDelayMinutes': '5', # 关机倒计时（分钟）
            'reminderIntervalSeconds': '300', # 提醒间隔（秒）
            'continuousUsageThreshold': '10', # 连续使用多久后强制休息（分钟）
            'forcedRestDuration': '1', # 强制休息时长（分钟）
            'forcedShutdownHour': '22', # 强制关机时间（小时）
            'adminPassword': 'admin' # 管理员密码
        }
        self.save_config()
        self.logger.info(f"Default '{self.CONFIG_FILE}' created.")

    def get_setting(self, section: str, key: str, type: Type = str, fallback: Optional[Any] = None) -> Optional[Any]:
        try:
            if type == bool:
                return self.config.getboolean(section, key)
            elif type == int:
                return self.config.getint(section, key)
            elif type == float:
                return self.config.getfloat(section, key)
            else:
                return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            self.logger.warning(f"Setting [{section}]{key} not found. Using fallback: {fallback}")
            return fallback
        except ValueError:
            self.logger.error(f"Error converting setting [{section}]{key} to type {type.__name__}. Using fallback: {fallback}")
            return fallback

    def set_setting(self, section: str, key: str, value: Any) -> None:
        if not self.config.has_section(section):
            self.config.add_section(section)
        # 确保保存的值是字符串类型
        self.config.set(section, key, str(value))
        self.logger.debug(f"Setting [{section}]{key} set to {value}")

    def save_config(self) -> None:
        try:
            # 确保以 utf-8 编码写入
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            self.logger.info(f"Configuration saved to {self.CONFIG_FILE}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")

    def get_section_settings(self, section: str) -> Dict[str, str]:
        """
        获取指定 section 下的所有键值对。
        返回一个字典。
        """
        if self.config.has_section(section):
            # configparser.items() 方法返回的是 (key, value) 对的列表
            # dict() 可以将其转换为字典
            return dict(self.config.items(section))
        self.logger.warning(f"Section '{section}' not found in config.")
        return {}

    def get_all_sections(self) -> List[str]:
        """
        获取所有 section 的名称列表。
        """
        return self.config.sections()

    def get_all_settings(self) -> Dict[str, Dict[str, str]]:
        """
        获取所有 section 的所有键值对，按 section 分组。
        返回一个嵌套字典，格式为 {section_name: {key: value, ...}, ...}。
        """
        all_data = {}
        for section in self.config.sections():
            all_data[section] = dict(self.config.items(section))
        return all_data