# **KidPC Monitor**

KidPC Monitor is a lightweight desktop application designed to help monitor computer usage, remind for breaks, and provide automated screenshots to a Telegram bot. It's particularly useful for parents who want to keep track of their children's computer activity and ensure healthy screen time habits.

## **Features**

* **Computer Usage Tracking**: Monitors and logs daily computer usage time.  
* **Floating Time Window**: An optional, always-on-top window displays today's total computer usage.  
* **Rest Reminders**: Customizable reminders for taking breaks after prolonged computer use, and warnings for late-night usage with optional automatic shutdown.  
* **Screenshot Capture & Telegram Integration**: Periodically takes screenshots of the computer screen and sends them to a configured Telegram bot, along with usage statistics and IP address.  
* **Hidden Operation**: Runs silently in the background, accessible via a system tray icon (Windows) or a hidden main window (macOS/Linux).  
* **Password-Protected Settings**: All configurations and password changes are protected by an administrator password.

## **Getting Started**

Follow these steps to set up and run KidPC Monitor on your computer.

### **Prerequisites**

* **Python 3.x**: Download and install Python from [python.org](https://www.python.org/downloads/). During installation, ensure you check the option to "Install Tcl/Tk and IDLE" (for Windows) to ensure Tkinter (the GUI library) works correctly.  
* **Telegram Bot Token & Chat ID**:  
  1. Create a new Telegram bot by talking to @BotFather on Telegram. Follow the instructions to get your **Bot Token**.  
  2. Find your **Chat ID**: You can use a bot like @userinfobot or simply forward a message from your new bot to a channel/group, and then use a Telegram Bot API tool (like visiting https://api.telegram.org/bot\<YOUR\_BOT\_TOKEN\>/getUpdates in your browser) to find the chat\_id from the JSON response.

### **Installation**

1. **Download the Project**: Get all the project files (e.g., main.py, config\_ui.py, config\_manager.py, config.ini, etc.) and place them in a single folder on your computer.  
2. **Install Dependencies**: Open a terminal or command prompt, navigate to the project folder, and install the required Python libraries using pip:  
   Bash  
   pip install pystray Pillow requests  
   *(Note: tkinter is usually included with Python, but if you encounter issues, ensure it's installed or your Python installation includes Tcl/Tk.)*  
3. **Place Icon File**: Ensure an image file named icon.png is placed in the same directory as your project files. This will be used for the system tray icon.

### **Configuration**

Before running the application, you need to configure config.ini:

1. **Open config.ini**: Use a text editor (like Notepad, VS Code, Sublime Text, etc.) to open the config.ini file in the project folder.  
2. **Edit \[Settings\] Section**:  
   * dataFolder: Where screenshots and usage statistics will be saved (e.g., .\\screenshots for a subfolder).  
   * botToken: **REQUIRED**. Paste your Telegram Bot Token here.  
   * chatId: **REQUIRED**. Paste your Telegram Chat ID here.  
   * proxy: (Optional) If you need to use a proxy for Telegram API requests (e.g., in regions where Telegram is blocked or for specific network setups), enter it here (e.g., 192.168.100.101:1081). Leave empty if not needed.  
   * screenshotInterval: How often screenshots are taken and sent (in minutes). Default is 1\.  
   * usageStatsFile: Path to the file where daily usage statistics are stored (e.g., .\\usage\_stats.json).  
   * showFloatWindow: Set to true to display the floating time window, or false to hide it.  
   * enableRestReminder: Set to true to enable rest reminders and automatic shutdown features, or false to disable them.  
   * firstReminderHour: Hour (24-hour format) for the first general rest reminder.  
   * shutdownPlanHour: Hour (24-hour format) when automatic shutdown planning begins.  
   * shutdownPlanMinute: Minute for the automatic shutdown planning.  
   * shutdownDelayMinutes: How many minutes after shutdownPlanHour:shutdownPlanMinute the computer will shut down if not cancelled.  
   * reminderIntervalSeconds: Interval (in seconds) between general rest reminders.  
   * continuousUsageThreshold: Continuous usage time (in minutes) after which a forced rest reminder is shown.  
   * forcedRestDuration: Duration (in minutes) of the forced rest period.  
   * forcedShutdownHour: Hour (24-hour format) for a hard forced shutdown.  
   * adminPassword: The password to access and modify settings. **Default is admin**. It is highly recommended to change this after the first run.

**Example config.ini:**Ini, TOML  
\[Settings\]  
dataFolder \= .\\screenshots  
botToken \= YOUR\_BOT\_TOKEN\_HERE  
chatId \= YOUR\_CHAT\_ID\_HERE  
proxy \=   
screenshotInterval \= 1  
usageStatsFile \= .\\usage\_stats.json  
showFloatWindow \= true  
enableRestReminder \= true  
firstReminderHour \= 21  
shutdownPlanHour \= 21  
shutdownPlanMinute \= 30  
shutdownDelayMinutes \= 5  
reminderIntervalSeconds \= 300  
continuousUsageThreshold \= 10  
forcedRestDuration \= 1  
forcedShutdownHour \= 22  
adminPassword \= admin

### **Running the Application**

1. **Open Terminal/Command Prompt**: Navigate to your project folder.  
2. **Run main.py**:  
   Bash  
   python main.py  
   The application will start in the background.

### **Using the Application**

Once running:

* **System Tray Icon**: On Windows, you will see a small icon in your system tray (near the clock). On macOS/Linux, the main window will be hidden, but the processes will be running. The system tray icon provides quick access to settings.  
* **Access Settings**:  
  * Right-click the system tray icon (Windows).  
  * Select "打开设置" (Open Settings) or "修改密码" (Change Password).  
  * You will be prompted to enter the administrator password (default is admin).  
  * After entering the correct password, the settings window will appear, where you can adjust any configuration. Remember to click "保存" (Save) to apply changes.  
* **Change Password**: You can change the administrator password from the system tray menu.  
* **Floating Time Window**: If showFloatWindow is true in config.ini, a small transparent window will appear on your screen, displaying the daily computer usage time. You can drag this window around.  
* **Rest Reminders**:  
  * **General Reminders**: At firstReminderHour (e.g., 9 PM), and then every reminderIntervalSeconds, you will receive a pop-up reminder to rest.  
  * **Planned Shutdown**: At shutdownPlanHour:shutdownPlanMinute (e.g., 9:30 PM), a pop-up will inform you that the computer will shut down in shutdownDelayMinutes. You can click "取消关机" (Cancel Shutdown) to prevent this.  
  * **Forced Rest**: If enableRestReminder is true and continuous usage exceeds continuousUsageThreshold, a full-screen "Forced Rest\!" window will appear for forcedRestDuration.  
  * **Forced Shutdown**: At forcedShutdownHour (e.g., 10 PM), the computer will automatically shut down regardless of current activity.  
* **Exit Application**: You can exit the application by right-clicking the system tray icon and selecting "退出" (Exit). This will stop all monitoring and sending activities.

## **Troubleshooting**

* **"icon.png not found\!" error**: Ensure icon.png is in the same directory as main.py.  
* **Tkinter GUI issues / ImportError**: If you encounter errors related to Tkinter (e.g., "Failed to setup env for tkinter"), it usually means your Python installation is missing the Tcl/Tk dependency. Reinstall Python and make sure to include Tcl/Tk.  
* **Telegram messages not sending**:  
  * Double-check your botToken and chatId in config.ini. They must be exact.  
  * Ensure your internet connection is active.  
  * If you are in a region with Telegram restrictions, try configuring the proxy in config.ini.  
  * Check screenshot\_bot.log for any error messages related to network requests.  
* **Application not running in background**: Ensure you are running main.py directly, not by double-clicking if it's opening a console window that closes. If you close the terminal window from which you started python main.py, the application will also close. For continuous background operation, consider converting it to an executable or using a background process manager (advanced topic).  
* **config.ini changes not taking effect**: After modifying config.ini directly, you need to restart the main.py application for the changes to load (unless changed via the GUI, which saves them immediately).