package com.example;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.IOException;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import com.google.gson.Gson;
import com.example.config.ConfigManager; // Import ConfigManager
import com.example.tracking.UsageTracker; // Import UsageTracker
import com.example.screenshot.ScreenshotTaker; // Import ScreenshotTaker
import com.example.communication.TelegramNotifier; // Import TelegramNotifier
import com.example.ui.TrayManager; // Import TrayManager
import com.example.ui.SettingsUI; // Import SettingsUI
import com.example.ui.FloatingUsageWindow; // Import FloatingUsageWindow
import com.example.reminder.RestReminderManager; // Import RestReminderManager

public class App {

    private OkHttpClient httpClient;
    private Gson gson;
    // private Timer reminderTimer; // Assuming this will be part of a specific feature later
    // private TrayIcon trayIcon; // Handled by TrayManager
    // private SystemTray systemTray; // Handled by TrayManager
    private ConfigManager configManager;
    private UsageTracker usageTracker;
    private ScreenshotTaker screenshotTaker;
    private TelegramNotifier telegramNotifier;
    private TrayManager trayManager;
    private SettingsUI settingsUI; // Add SettingsUI instance
    private FloatingUsageWindow floatingUsageWindow; // Add FloatingUsageWindow instance
    private RestReminderManager restReminderManager; // Add RestReminderManager instance
    private JFrame mainFrame; // Keep a reference if needed for show/hide

    public App() {
        configManager = new ConfigManager("my-app-config");
        usageTracker = new UsageTracker(configManager);
        screenshotTaker = new ScreenshotTaker(configManager);
        telegramNotifier = new TelegramNotifier(configManager, usageTracker, screenshotTaker);
        trayManager = new TrayManager(this); // Pass 'this' App instance
        settingsUI = new SettingsUI(configManager); // Initialize SettingsUI
        floatingUsageWindow = new FloatingUsageWindow(configManager, usageTracker); // Initialize FloatingUsageWindow
        // Pass mainFrame to RestReminderManager if it's already created,
        // or ensure mainFrame is created before RestReminderManager if it needs it for dialog parenting.
        // For now, passing null or delaying RestReminderManager instantiation might be needed if mainFrame isn't ready.
        // Let's assume mainFrame is created first, then RestReminderManager.
        
        createAndShowGUI(); // Create mainFrame first

        restReminderManager = new RestReminderManager(configManager, usageTracker, mainFrame); // Initialize RestReminderManager

        usageTracker.startTracking();
        restReminderManager.start(); // Start reminder checks

        httpClient = new OkHttpClient();
        gson = new Gson();

        // createAndShowGUI(); // Moved up to ensure mainFrame exists for RestReminderManager
        trayManager.setupTrayIcon();
        
        // Initialize and show the floating window if enabled
        if (configManager.getBoolean("showFloatWindow", true)) {
            floatingUsageWindow.initializeAndShow();
        }


        System.out.println("Screenshot Interval from config: " + configManager.getInt("screenshotInterval", 60));

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            if (restReminderManager != null) {
                restReminderManager.stop(); // Stop reminders and abort any OS shutdown
            }
            if (usageTracker != null) {
                usageTracker.stopTracking();
            }
            if (trayManager != null) {
                trayManager.removeTrayIcon();
            }
            if (floatingUsageWindow != null) {
                floatingUsageWindow.disposeWindow();
            }
            // Dispose GUI elements if any
            if (mainFrame != null) {
                mainFrame.dispose();
            }
            System.out.println("Application shutting down.");
        }));
    }

    private void createAndShowGUI() {
        mainFrame = new JFrame("REST Reminder"); // Assign to mainFrame
        mainFrame.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE); // Prevent accidental close, rely on tray exit
        mainFrame.setSize(400, 300); // Adjusted size
        mainFrame.setLayout(new FlowLayout());
        mainFrame.setLocationRelativeTo(null); // Center on screen

        JLabel label = new JLabel("REST Reminder Application (Control via System Tray)");
        mainFrame.add(label);

        JButton testButton = new JButton("Fetch Data (Test)");
        testButton.addActionListener(e -> fetchDataFromAPI());
        mainFrame.add(testButton);

        JButton screenshotButton = new JButton("Take Screenshot (Test)");
        screenshotButton.addActionListener(e -> {
            String path = screenshotTaker.takeScreenshot();
            if (path != null) {
                System.out.println("Screenshot taken: " + path);
                // trayManager.displayMessage(...) could be a new method in TrayManager
                // For now, direct display if trayIcon reference was available, or use sout
            }
        });
        mainFrame.add(screenshotButton);

        JButton notifyButton = new JButton("Send Notification (Test)");
        notifyButton.addActionListener(e -> {
            boolean success = telegramNotifier.sendScreenshotWithDetails();
            System.out.println("Test notification sent: " + success);
        });
        mainFrame.add(notifyButton);
        
        // Initially hide the main window, can be shown from tray or settings
        mainFrame.setVisible(false); 
    }

    // Placeholder methods to be called by TrayManager or other UI components
    public void showSettingsWindow() {
        System.out.println("App: showSettingsWindow() called");
        SwingUtilities.invokeLater(() -> settingsUI.displaySettings());
    }

    public void showChangePasswordDialog() {
        System.out.println("App: showChangePasswordDialog() called");
        // The SettingsUI's change password dialog might be better called from within settings,
        // or if called from tray, it needs a parent component (can be null or the hidden mainFrame).
        SwingUtilities.invokeLater(() -> settingsUI.displayChangePasswordDialog(mainFrame));
    }

    public void exitApplication() {
        System.out.println("App: exitApplication() called");
        // The shutdown hook will handle cleanup (tracker.stop, tray.remove)
        System.exit(0);
    }


    private void fetchDataFromAPI() { // Kept for testing button
        Request request = new Request.Builder()
                .url("https://jsonplaceholder.typicode.com/todos/1") // Example API
                .build();
        try (Response response = httpClient.newCall(request).execute()) {
            if (response.isSuccessful() && response.body() != null) {
                String responseData = response.body().string();
                System.out.println("Fetched data: " + responseData);
                 // trayManager.displayMessage("API Data", "Fetched successfully!", TrayIcon.MessageType.INFO);
            } else {
                 // trayManager.displayMessage("API Error", "Failed to fetch data: " + response.message(), TrayIcon.MessageType.ERROR);
                 System.err.println("API Error: Failed to fetch data: " + response.message());
            }
        } catch (IOException e) {
            e.printStackTrace();
            // trayManager.displayMessage("API Exception", "Error: " + e.getMessage(), TrayIcon.MessageType.ERROR);
             System.err.println("API Exception: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        // Ensures that the AWT toolkit is initialized, especially for headless environments
        // where SystemTray might be accessed early.
        Toolkit.getDefaultToolkit(); 

        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                new App(); // Initializes ConfigManager, Tracker, Notifier, TrayManager
            }
        });
    }

    // Example data class for Gson (currently unused, can be removed if not needed)
    // static class MyData {
    //     int userId;
    //     int id;
    //     String title;
    //     boolean completed;
    //
    //     @Override
    //     public String toString() {
    //         return "MyData{" +
    //                 "userId=" + userId +
    //                 ", id=" + id +
    //                 ", title='" + title + '\'' +
    //                 ", completed=" + completed +
    //                 '}';
    //     }
    // }
}
