# 儿童电脑使用管理系统

## 项目简介

儿童电脑使用管理系统是一款专为家长设计的工具，用于帮助监控和管理孩子的电脑使用习惯。该系统通过记录使用时间、发送截图和强制休息提醒，帮助家长引导孩子健康使用电子设备，培养良好的数字习惯。

## 核心功能

**时间管理**

记录每日累计使用时间和连续使用时间

自定义使用时间阈值和休息时间

晚间自动关机功能，确保充足睡眠

**强制休息提醒**

当连续使用时间超过设定值时，自动弹出不可关闭的休息窗口

休息时间结束后自动恢复使用

支持自定义休息时长

**远程监控**

定时截取屏幕并发送至家长的 Telegram 账号

截图附带详细的使用时间信息

支持通过代理服务器连接，确保网络稳定性

**友好界面**

半透明浮动窗口显示使用时间，不干扰正常操作

简洁明了的倒计时显示

支持中文界面，操作简单直观

## 项目结构



```
kidPC/

├── main.py               # 主程序入口

├── rest\_reminder.py      # 休息提醒模块

├── usage\_tracker.py      # 使用时间跟踪模块

├── float\_window.py       # 浮动窗口显示模块

├── screenshot\_sender.py  # 截图发送模块

├── run.bat               # Windows启动脚本

├── config.ini            # 配置文件

├── usage\_stats.json      # 使用数据存储

├── .gitignore            # Git忽略配置

└── logs/                 # 日志文件夹
```

## 配置说明

修改`config.ini`文件可自定义系统行为：



```
\[Settings]

dataFolder = data                 # 数据存储文件夹

usageStatsFile = usage\_stats.json # 使用数据文件

eveningStartHour = 21             # 晚间开始时间(小时)

lateEveningStartHour = 21         # 深夜开始时间(小时)

lateEveningStartMinute = 30       # 深夜开始时间(分钟)

shutdownDelayMinutes = 5          # 关机前倒计时(分钟)

reminderIntervalSeconds = 300     # 提醒间隔(秒)

continuousUsageThreshold = 45     # 连续使用阈值(分钟)

forcedRestDuration = 5            # 强制休息时间(分钟)

botToken = your\_telegram\_bot\_token # Telegram机器人令牌

chatId = your\_chat\_id             # 接收消息的Telegram聊天ID

proxy = socks5://127.0.0.1:1080   # 代理服务器地址(可选)

screenshotInterval = 1            # 截图间隔(分钟)

showFloatWindow = true            # 是否显示浮动窗口
```

## 安装与使用

**安装依赖**



```
pip install pillow python-telegram-bot
```

**配置 Telegram 机器人 (可选)**

创建 Telegram 机器人并获取令牌

获取接收消息的聊天 ID

在`config.ini`中填写`botToken`和`chatId`

**启动程序**

双击`run.bat`(Windows)

或运行命令：`python ``main.py`

## 家长指南

**查看使用报告**：通过查看`usage_stats.json`了解孩子的电脑使用习惯

**远程监控**：通过 Telegram 接收孩子的屏幕截图和使用时间报告

**调整设置**：修改`config.ini`中的参数，调整使用时间限制和提醒频率

**紧急控制**：通过关闭`run.bat`或结束`python ``main.py`进程立即停止程序

## 儿童体验

清晰可见的使用时间提醒

友好的休息提示界面

强制休息期间可进行眼部放松活动

培养健康的电脑使用习惯

## 技术实现

系统采用模块化设计，各组件分工明确：

`usage_tracker.py`：精确记录使用时间，处理跨天统计

`rest_reminder.py`：管理休息提醒和关机计划

`float_window.py`：创建半透明浮动窗口显示使用时间

`screenshot_sender.py`：定时截图并发送至指定 Telegram 聊天

## 贡献与支持

如果您有任何建议或发现问题，请提交 Issue 或 Pull Request。我们欢迎所有有助于提升儿童数字健康的贡献！