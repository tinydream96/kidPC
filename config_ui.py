import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import pystray
from PIL import Image
import threading
import logging

# 导入 ConfigManager，确保 main.py 已经将它实例化并传递给 ConfigUI
# from config_manager import ConfigManager # 不再需要直接导入，因为会作为参数传入

logger = logging.getLogger("ConfigUI")

# --- 修改开始: 增加UI字符串 ---
UI_STRINGS = {
    'zh_CN': {
        'error_title': "错误",
        'icon_not_found_message': "icon.png 未找到！请确保图标文件在程序同目录。",
        'menu_open_settings': "打开设置",
        'menu_change_password': "修改密码",
        'menu_exit': "退出",
        'config_window_title': "配置设置",
        'password_prompt_title': "密码验证",
        'password_prompt_label': "请输入密码：",
        'exit_password_prompt': "请输入密码以退出程序：", # 新增
        'password_error_message': "密码错误！",
        'save_button_text': "保存",
        'info_title': "提示",
        'config_saved_message': "配置已保存！",
        'current_password_prompt': "请输入当前密码：",
        'new_password_prompt': "请输入新密码：",
        'password_changed_message': "密码已修改！",
        'new_password_empty_message': "新密码不能为空。",
    }
}
# --- 修改结束 ---


class ConfigUI:
    def get_string(self, key, lang='zh_CN'):
        return UI_STRINGS.get(lang, {}).get(key, f"Missing string: {key}")

    # 接收 main.py 的主 Tkinter 根窗口 (root) 和 ConfigManager 实例
    # 接收 main.py 的主 Tkinter 根窗口 (root) 和 ConfigManager 实例
    def __init__(self, main_root, config_manager):
        self.root = main_root  # 使用主 root 作为 Toplevel 的父窗口
        self.config_manager = config_manager  # 使用统一的 ConfigManager

        # 从 ConfigManager 读取密码
        # 注意：这里使用 'adminPassword'，请确保 config.ini 和 ConfigManager 中的键名一致
        self.password = self.config_manager.get_setting('Settings', 'adminPassword', fallback='admin')
        logger.info(f"ConfigUI initialized. Password loaded: {self.password}")

        self.tray = None  # 初始化为 None
        self.create_tray_icon()  # 创建托盘图标

    def create_tray_icon(self):
        try:
            image = Image.open("icon.png")
            logger.info("Tray icon image loaded.")
        except FileNotFoundError:
            # 托盘图标找不到时不阻止程序启动，但给出错误提示
            messagebox.showerror(self.get_string('error_title'), self.get_string('icon_not_found_message'), parent=self.root)
            logger.error("Tray icon file 'icon.png' not found.")
            # return # 移除 return，允许程序继续运行，只是没有托盘图标
            # 如果没有图标，可以尝试使用默认图标或者不创建托盘
            # 为了程序健壮性，这里暂时可以不 return，但后续UI可能依赖tray的存在
            # 最好的做法是在没有图标时，让 ConfigUI 的创建者（main.py）决定如何处理
            return  # 暂时保留 return，确保不会因为图标问题导致后续错误

        menu = (
            pystray.MenuItem(self.get_string('menu_open_settings'), self._schedule_open_settings),  # 调度到主线程
            pystray.MenuItem(self.get_string('menu_change_password'), self._schedule_change_password),  # 调度到主线程
            pystray.MenuItem(self.get_string('menu_exit'), self._schedule_quit_app)  # 调度到主线程
        )
        self.tray = pystray.Icon("config_ui", image, self.get_string('config_window_title'), menu)

        # 托盘图标本身运行在一个独立的守护线程中
        # 只有在 main.py 的根窗口启动后，托盘图标才能正常工作
        threading.Thread(target=self.tray.run, daemon=True).start()
        logger.info("Tray icon thread started.")

    # 调度到主线程，避免Tkinter在非主线程操作UI
    def _schedule_open_settings(self):
        self.root.after(0, self.open_settings)

    def open_settings(self):
        # 暂时显示主窗口作为simpledialog的父窗口，解决macOS上无法显示对话框的问题
        self.root.deiconify()
        password = simpledialog.askstring(self.get_string('password_prompt_title'), self.get_string('password_prompt_label'), show='*', parent=self.root)
        self.root.withdraw()  # 对话框结束后立即隐藏主窗口

        if password == self.password:
            self.show_settings_window()
            logger.info("Password correct. Opening settings window.")
        else:
            messagebox.showerror(self.get_string('error_title'), self.get_string('password_error_message'), parent=self.root)
            logger.warning("Incorrect password entered for settings.")

    def show_settings_window(self):
        # 使用 Toplevel 作为设置窗口，而不是 Tk
        settings_window = tk.Toplevel(self.root)
        settings_window.title(self.get_string('config_window_title'))
        # 设置窗口居中（可选）
        settings_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() / 2) - (settings_window.winfo_width() / 2)
        y = self.root.winfo_y() + (self.root.winfo_height() / 2) - (settings_window.winfo_height() / 2)
        settings_window.geometry(f'+{int(x)}+{int(y)}')

        logger.info("Settings window created (Toplevel).")

        # 修正：从 ConfigManager 获取 'Settings' 部分的所有配置项
        # 调用 get_section_settings 方法，并传入 'Settings' 作为参数
        all_settings_in_section = self.config_manager.get_section_settings('Settings')

        row = 0
        self.entries = {}
        # 遍历 'Settings' 部分的键值对
        for key, value in all_settings_in_section.items():
            # 密码字段特殊处理，不显示实际值，只显示星号
            # 注意：configparser 默认会将键转换为小写，所以这里也用小写匹配
            if key.lower() == 'adminpassword':
                tk.Label(settings_window, text=key).grid(row=row, column=0, padx=5, pady=2, sticky='w')
                entry = tk.Entry(settings_window, show='*')  # 密码显示星号
                entry.insert(0, value)  # 插入当前值，但只显示星号
                entry.grid(row=row, column=1, padx=5, pady=2, sticky='ew')
                self.entries[key] = entry
            else:
                tk.Label(settings_window, text=key).grid(row=row, column=0, padx=5, pady=2, sticky='w')
                entry = tk.Entry(settings_window)
                entry.insert(0, str(value))  # 确保插入的是字符串
                entry.grid(row=row, column=1, padx=5, pady=2, sticky='ew')
                self.entries[key] = entry
            row += 1

        # 保存按钮
        save_button = tk.Button(settings_window, text=self.get_string('save_button_text'), command=lambda: self.save_config(settings_window))
        save_button.grid(row=row, column=0, columnspan=2, pady=10)
        logger.debug("Save button added to settings window.")

        # 确保窗口关闭时销毁
        settings_window.protocol("WM_DELETE_WINDOW", lambda: self._on_settings_window_close(settings_window))

    def _on_settings_window_close(self, window):
        logger.info("Settings window closed.")
        window.destroy()

    def save_config(self, window):
        for key, entry in self.entries.items():
            value = entry.get()
            # 注意：configparser 默认会将键转换为小写，所以这里也用小写匹配
            if key.lower() == 'adminpassword':
                # 只有当用户输入新密码且与当前密码不同时才更新
                if value != self.password:
                    self.config_manager.set_setting('Settings', key, value)
                    self.password = value  # 更新内存中的密码
            else:
                self.config_manager.set_setting('Settings', key, value)

        self.config_manager.save_config()  # 统一通过 ConfigManager 保存
        messagebox.showinfo(self.get_string('info_title'), self.get_string('config_saved_message'), parent=window)
        logger.info("Configuration saved successfully.")
        window.destroy()

    # 调度到主线程
    def _schedule_change_password(self):
        self.root.after(0, self.change_password)

    def change_password(self):
        self.root.deiconify()  # 暂时显示主窗口
        old_password = simpledialog.askstring(self.get_string('password_prompt_title'), self.get_string('current_password_prompt'), show='*', parent=self.root)
        self.root.withdraw()  # 隐藏主窗口

        if old_password == self.password:
            self.root.deiconify()  # 暂时显示主窗口
            new_password = simpledialog.askstring(self.get_string('menu_change_password'), self.get_string('new_password_prompt'), show='*', parent=self.root)
            self.root.withdraw()  # 隐藏主窗口

            if new_password:
                self.password = new_password
                # 注意：configparser 默认会将键转换为小写，所以这里也用小写匹配
                self.config_manager.set_setting('Settings', 'adminPassword', new_password)
                self.config_manager.save_config()  # 保存到文件
                messagebox.showinfo(self.get_string('info_title'), self.get_string('password_changed_message'), parent=self.root)
                logger.info("Admin password changed successfully.")
            else:
                messagebox.showinfo(self.get_string('info_title'), self.get_string('new_password_empty_message'), parent=self.root)
                logger.warning("New password was empty.")
        else:
            messagebox.showerror(self.get_string('error_title'), self.get_string('password_error_message'), parent=self.root)
            logger.warning("Incorrect password entered for password change.")

    # 调度到主线程
    def _schedule_quit_app(self):
        self.root.after(0, self.quit_app)

    # --- 修改开始: 重写 quit_app 方法 ---
    def quit_app(self):
        """
        在退出程序前请求密码验证。
        """
        self.root.deiconify()
        password = simpledialog.askstring(
            self.get_string('password_prompt_title'),
            self.get_string('exit_password_prompt'),  # 使用新的提示语
            show='*',
            parent=self.root
        )
        self.root.withdraw()

        # 检查密码是否正确
        if password == self.password:
            logger.info("Correct password entered. Quitting application via tray icon.")
            if self.tray:
                self.tray.stop()
                logger.debug("Tray icon stopped.")
            # 通知主 Tkinter 根窗口销毁
            if self.root:
                self.root.quit()  # 使用 quit() 来停止 mainloop
                logger.debug("Main Tkinter root quit signaled.")
        # 如果用户输入了密码但错误
        elif password is not None:
            messagebox.showerror(
                self.get_string('error_title'),
                self.get_string('password_error_message'),
                parent=self.root
            )
            logger.warning("Incorrect password entered for quitting.")
        # 如果用户点击了取消(password is None)，则不执行任何操作
        else:
            logger.info("Quit operation cancelled by user.")
    # --- 修改结束 ---