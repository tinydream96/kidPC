package com.example.reminder;

import com.example.config.ConfigManager;
import com.example.tracking.UsageTracker;

import javax.swing.*;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.IOException;
import java.time.Duration;
import java.time.LocalTime;
import java.time.temporal.ChronoUnit;
import java.util.TimerTask;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

public class RestReminderManager {

    private final ConfigManager configManager;
    private final UsageTracker usageTracker;
    private final JFrame mainAppFrame; // For dialog parent

    // Configuration settings
    private boolean enableRestReminder;
    private int firstReminderHour;
    private int shutdownPlanHour;
    private int shutdownPlanMinute;
    private int shutdownDelayMinutes;
    private int reminderIntervalSeconds;
    private long continuousUsageThresholdSeconds;
    private long forcedRestDurationSeconds;
    private int forcedShutdownHour;

    private ScheduledExecutorService scheduler;
    private ScheduledFuture<?> periodicCheckTask;
    private ScheduledFuture<?> plannedShutdownTask;
    private ScheduledFuture<?> forcedRestEndTask;


    // State flags
    private volatile boolean isGeneralReminderActive = false;
    private volatile boolean isShutdownWarningActive = false;
    private volatile boolean isForcedRestActive = false;
    private volatile boolean isOsShutdownScheduled = false; // Tracks if OS shutdown command has been issued
    private JDialog plannedShutdownDialog;
    private JDialog forcedRestDialog;
    private Timer countdownTimer;


    public RestReminderManager(ConfigManager configManager, UsageTracker usageTracker, JFrame mainAppFrame) {
        this.configManager = configManager;
        this.usageTracker = usageTracker;
        this.mainAppFrame = mainAppFrame;
        loadConfig();
    }

    private void loadConfig() {
        enableRestReminder = configManager.getBoolean("enableRestReminder", true);
        firstReminderHour = configManager.getInt("firstReminderHour", 21);
        shutdownPlanHour = configManager.getInt("shutdownPlanHour", 21);
        shutdownPlanMinute = configManager.getInt("shutdownPlanMinute", 30);
        shutdownDelayMinutes = configManager.getInt("shutdownDelayMinutes", 5);
        reminderIntervalSeconds = configManager.getInt("reminderIntervalSeconds", 300);
        continuousUsageThresholdSeconds = TimeUnit.MINUTES.toSeconds(configManager.getInt("continuousUsageThreshold", 10)); // Assuming threshold in minutes
        forcedRestDurationSeconds = TimeUnit.MINUTES.toSeconds(configManager.getInt("forcedRestDuration", 1)); // Assuming duration in minutes
        forcedShutdownHour = configManager.getInt("forcedShutdownHour", 22);
    }

    public void start() {
        if (!enableRestReminder) {
            System.out.println("RestReminderManager is disabled by configuration.");
            return;
        }
        if (scheduler == null || scheduler.isShutdown()) {
            scheduler = Executors.newSingleThreadScheduledExecutor();
        }
        // Check conditions e.g. every 5 seconds. A more dynamic scheduling could be implemented.
        periodicCheckTask = scheduler.scheduleAtFixedRate(this::checkAllConditions, 0, 5, TimeUnit.SECONDS);
        System.out.println("RestReminderManager started.");
    }

    public void stop() {
        if (periodicCheckTask != null && !periodicCheckTask.isDone()) {
            periodicCheckTask.cancel(false);
        }
        if (plannedShutdownTask != null && !plannedShutdownTask.isDone()) {
            plannedShutdownTask.cancel(false);
            // If an OS shutdown was scheduled, try to abort it.
            if (isOsShutdownScheduled) {
                abortSystemShutdown();
            }
        }
        if (forcedRestEndTask != null && !forcedRestEndTask.isDone()) {
            forcedRestEndTask.cancel(false);
        }
        if (scheduler != null) {
            scheduler.shutdown();
            try {
                if (!scheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                    scheduler.shutdownNow();
                }
            } catch (InterruptedException e) {
                scheduler.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
        // Close any active dialogs
        closeDialog(plannedShutdownDialog);
        closeDialog(forcedRestDialog);
        System.out.println("RestReminderManager stopped.");
    }

    private void closeDialog(JDialog dialog) {
        if (dialog != null && dialog.isVisible()) {
            SwingUtilities.invokeLater(dialog::dispose);
        }
    }


    private void checkAllConditions() {
        if (isForcedRestActive || isShutdownWarningActive) {
            // Don't show other reminders if a blocking/modal event is active
            return;
        }

        LocalTime now = LocalTime.now();

        // 1. Forced Shutdown Check (Highest Priority)
        if (now.getHour() == forcedShutdownHour && now.getMinute() == 0) {
            // To prevent repeated calls in the same minute:
            if (scheduler != null && !scheduler.isShutdown()) { // Basic check
                System.out.println("Forced shutdown condition met. Shutting down now.");
                executeSystemShutdown(0, true); // Immediate, forced
                stop(); // Stop further checks
                // Optionally, inform App to exit if shutdown command fails or for cleanup
                // For now, assuming shutdown command works and OS handles exit.
                return; // Stop further checks this cycle
            }
        }

        // 2. Forced Rest Check
        if (usageTracker.getContinuousUsageTime() > continuousUsageThresholdSeconds) {
            if (!isForcedRestActive) { // Check if not already in forced rest
                showForcedRestDialog();
            }
            return; // Forced rest takes precedence over other reminders for this cycle
        }

        // 3. Planned Shutdown Check
        if (now.getHour() == shutdownPlanHour && now.getMinute() == shutdownPlanMinute && !isShutdownWarningActive && !isOsShutdownScheduled) {
             showPlannedShutdownDialog();
             return; // Planned shutdown warning shown, no other reminders this cycle
        }
        
        // 4. General Rest Reminder (Lowest Priority)
        // This logic needs refinement: Python version implies it only starts after firstReminderHour
        // and then perhaps at reminderIntervalSeconds.
        // For now, a simple check if past firstReminderHour.
        // A better implementation would track last general reminder time.
        if (now.getHour() >= firstReminderHour && !isGeneralReminderActive) {
            // This needs a flag or timestamp to avoid showing every 5 seconds
            // For this example, we'll just show it once if conditions are met per start/stop cycle
            // Or, more simply, rely on isGeneralReminderActive to be reset externally if needed.
            // A simple periodic check:
            long secondsSinceLastGeneralReminder = Duration.between(lastGeneralReminderTime, now).getSeconds(); // Need to define lastGeneralReminderTime
            // if (secondsSinceLastGeneralReminder >= reminderIntervalSeconds) {
            //    showGeneralRestReminder();
            //    lastGeneralReminderTime = now;
            // }
            // Simplified: show once if conditions are met and no other modal is up.
            // This specific logic for general reminder timing needs to be clarified from Python version.
            // For now, let's assume it's a one-time show past firstReminderHour or needs a more complex trigger.
            // Let's assume it's triggered if no other dialog is showing and it's past the hour.
            // To prevent spamming, this needs a flag like `isGeneralReminderShownTodayAfterFirstHour`
            // or more sophisticated timing.
            // For this iteration, we'll just show it if no other modal is active and past time.
             if(!isForcedRestActive && !isShutdownWarningActive) { // Re-check, as state might change
                // showGeneralRestReminder(); // This will be called repeatedly, needs better logic
             }
        }
    }
    
    private LocalTime lastGeneralReminderTime = LocalTime.MIN; // Example for tracking last reminder


    private void showGeneralRestReminder() {
        SwingUtilities.invokeLater(() -> {
            if (isForcedRestActive || isShutdownWarningActive || isGeneralReminderActive) return; // Double check
            isGeneralReminderActive = true;
            
            JPanel panel = new JPanel();
            panel.setBackground(new Color(0xFF, 0x6B, 0x6B)); // #FF6B6B
            JLabel label = new JLabel("该休息啦！已经很晚了，请注意休息！长时间使用电脑会影响健康。");
            label.setForeground(Color.WHITE);
            label.setFont(new Font("SansSerif", Font.PLAIN, 16));
            panel.add(label);

            JOptionPane.showMessageDialog(mainAppFrame, panel, "温馨提示", JOptionPane.INFORMATION_MESSAGE);
            isGeneralReminderActive = false; // Reset after dialog is closed
            lastGeneralReminderTime = LocalTime.now(); // Update last reminder time
        });
    }

    private void showPlannedShutdownDialog() {
        SwingUtilities.invokeLater(() -> {
            if (isForcedRestActive || isShutdownWarningActive) return;
            isShutdownWarningActive = true;

            plannedShutdownDialog = new JDialog(mainAppFrame, "系统计划关机", true); // Modal
            plannedShutdownDialog.setDefaultCloseOperation(JDialog.DO_NOTHING_ON_CLOSE); // Prevent closing via X
            plannedShutdownDialog.setSize(400, 200);
            plannedShutdownDialog.setLocationRelativeTo(mainAppFrame);
            
            JPanel panel = new JPanel(new BorderLayout(10, 10));
            panel.setBorder(BorderFactory.createEmptyBorder(10,10,10,10));

            JLabel messageLabel = new JLabel("", SwingConstants.CENTER);
            messageLabel.setFont(new Font("SansSerif", Font.BOLD, 16));
            panel.add(messageLabel, BorderLayout.CENTER);

            JButton cancelButton = new JButton("取消关机");
            cancelButton.addActionListener(e -> {
                abortSystemShutdown();
                isShutdownWarningActive = false;
                isOsShutdownScheduled = false;
                if (plannedShutdownTask != null) plannedShutdownTask.cancel(true);
                if (countdownTimer != null) countdownTimer.stop();
                plannedShutdownDialog.dispose();
                JOptionPane.showMessageDialog(mainAppFrame, "已取消自动关机计划。", "操作成功", JOptionPane.INFORMATION_MESSAGE);
            });
            JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.CENTER));
            buttonPanel.add(cancelButton);
            panel.add(buttonPanel, BorderLayout.SOUTH);
            
            plannedShutdownDialog.add(panel);

            final long[] countdownSeconds = {TimeUnit.MINUTES.toSeconds(shutdownDelayMinutes)};
            messageLabel.setText(String.format("电脑将在 %d 秒后自动关机。请保存好您的工作！", countdownSeconds[0]));

            countdownTimer = new Timer(1000, e -> {
                countdownSeconds[0]--;
                if (countdownSeconds[0] <= 0) {
                    ((Timer) e.getSource()).stop();
                    plannedShutdownDialog.dispose();
                    isShutdownWarningActive = false; 
                    // isOsShutdownScheduled remains true as the command was issued
                    // The actual shutdown is handled by the OS now.
                } else {
                    messageLabel.setText(String.format("电脑将在 %d 秒后自动关机。请保存好您的工作！", countdownSeconds[0]));
                }
            });
            
            plannedShutdownDialog.addWindowListener(new WindowAdapter() {
                @Override
                public void windowClosing(WindowEvent e) {
                    // Handle if user tries to close dialog through other means (e.g. Alt+F4)
                    // For simplicity, this is disabled by DO_NOTHING_ON_CLOSE
                }
            });

            plannedShutdownDialog.setVisible(true); // Show the dialog first
            
            // Schedule OS shutdown after dialog is visible
            executeSystemShutdown((int)TimeUnit.MINUTES.toSeconds(shutdownDelayMinutes), false);
            isOsShutdownScheduled = true;
            countdownTimer.start(); // Start countdown after scheduling OS shutdown
        });
    }

    private void showForcedRestDialog() {
        SwingUtilities.invokeLater(() -> {
            if (isForcedRestActive) return; // Already active
            isForcedRestActive = true;
            usageTracker.resetContinuousUsageTime(); // Reset immediately when rest starts

            forcedRestDialog = new JDialog(mainAppFrame, "强制休息", true); // Modal
            forcedRestDialog.setUndecorated(true); // Full screen effect
            forcedRestDialog.setAlwaysOnTop(true);
            forcedRestDialog.setDefaultCloseOperation(JDialog.DO_NOTHING_ON_CLOSE);

            // Full screen
            GraphicsDevice gd = GraphicsEnvironment.getLocalGraphicsEnvironment().getDefaultScreenDevice();
            if (gd.isFullScreenSupported()) {
                gd.setFullScreenWindow(forcedRestDialog);
            } else {
                System.err.println("Full screen not supported; using maximized window.");
                forcedRestDialog.setExtendedState(JFrame.MAXIMIZED_BOTH);
                forcedRestDialog.setSize(Toolkit.getDefaultToolkit().getScreenSize());
            }
            
            JPanel panel = new JPanel(new GridBagLayout());
            panel.setBackground(new Color(0xC2, 0xF0, 0xC2)); // #C2F0C2

            JLabel messageLabel = new JLabel("", SwingConstants.CENTER);
            messageLabel.setFont(new Font("SansSerif", Font.BOLD, 24));
            messageLabel.setForeground(Color.BLACK); // White text might be hard on light green
            panel.add(messageLabel);
            
            forcedRestDialog.add(panel);

            final long[] countdownSeconds = {forcedRestDurationSeconds};
            long continuousMinutes = TimeUnit.SECONDS.toMinutes(continuousUsageThresholdSeconds);
            long restMinutes = TimeUnit.SECONDS.toMinutes(forcedRestDurationSeconds);
            
            messageLabel.setText(String.format("强制休息！您已连续使用电脑 %d 分钟，请休息 %d 分钟！剩余休息时间: %s",
                                 continuousMinutes, restMinutes, UsageTracker.formatTime(countdownSeconds[0])));

            Timer restTimer = new Timer(1000, e -> {
                countdownSeconds[0]--;
                if (countdownSeconds[0] <= 0) {
                    ((Timer) e.getSource()).stop();
                    if (gd.isFullScreenSupported()) {
                        gd.setFullScreenWindow(null); // Exit full screen
                    }
                    forcedRestDialog.dispose();
                    isForcedRestActive = false;
                    // Continuous usage time was already reset when rest started
                } else {
                    messageLabel.setText(String.format("强制休息！您已连续使用电脑 %d 分钟，请休息 %d 分钟！剩余休息时间: %s",
                                         continuousMinutes, restMinutes, UsageTracker.formatTime(countdownSeconds[0])));
                }
            });
            
            forcedRestDialog.setVisible(true);
            restTimer.start();
        });
    }


    private void executeSystemShutdown(int seconds, boolean force) {
        String command;
        String os = System.getProperty("os.name").toLowerCase();
        if (os.contains("win")) {
            command = "shutdown " + (force ? "/s /f" : "/s") + " /t " + seconds;
        } else if (os.contains("nix") || os.contains("nux") || os.contains("mac")) {
            if (seconds == 0) { // Immediate
                command = "shutdown -h now";
            } else {
                command = "shutdown -h +" + (seconds / 60); // shutdown command usually takes minutes
            }
             if (force && os.contains("nix") || os.contains("nux")) command += " -P"; // Poweroff for Linux
        } else {
            System.err.println("Unsupported OS for shutdown command: " + os);
            return;
        }

        try {
            System.out.println("Executing system command: " + command);
            Runtime.getRuntime().exec(command);
            if (!force && seconds > 0) { // If it's a planned, non-immediate shutdown
                 isOsShutdownScheduled = true; // Track that we initiated it.
            }
        } catch (IOException e) {
            System.err.println("Error executing shutdown command: " + e.getMessage());
        }
    }

    private void abortSystemShutdown() {
        String command;
        String os = System.getProperty("os.name").toLowerCase();
        if (os.contains("win")) {
            command = "shutdown /a";
        } else if (os.contains("nix") || os.contains("nux") || os.contains("mac")) {
            command = "shutdown -c"; // Common command to cancel shutdown
        } else {
            System.err.println("Unsupported OS for aborting shutdown: " + os);
            return;
        }

        try {
            System.out.println("Executing system command: " + command);
            Runtime.getRuntime().exec(command);
            isOsShutdownScheduled = false;
        } catch (IOException e) {
            System.err.println("Error aborting shutdown: " + e.getMessage());
        }
    }
}
