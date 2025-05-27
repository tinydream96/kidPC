package com.example.ui;

import com.example.config.ConfigManager;
import com.example.tracking.UsageTracker;

import javax.swing.*;
import java.awt.*;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

public class FloatingUsageWindow {

    private final ConfigManager configManager;
    private final UsageTracker usageTracker;
    private JWindow window;
    private JLabel timeLabel;
    private Timer updateTimer;
    private Point initialClick; // For dragging

    public FloatingUsageWindow(ConfigManager configManager, UsageTracker usageTracker) {
        this.configManager = configManager;
        this.usageTracker = usageTracker;
    }

    public void initializeAndShow() {
        if (!configManager.getBoolean("showFloatWindow", true)) {
            System.out.println("Floating window is disabled in config.");
            return;
        }

        // Ensure creation on EDT
        SwingUtilities.invokeLater(() -> {
            window = new JWindow();
            window.setAlwaysOnTop(true);
            window.setFocusableWindowState(false); // Prevent it from taking focus

            // Attempt to set opacity (might not work on all platforms/Java versions without full LAF support for it)
            try {
                 if (window.isOpacitySupported()) { // Check if opacity is supported
                    window.setOpacity(0.75f);
                 } else {
                    System.out.println("Window opacity not supported by current graphics environment.");
                 }
            } catch (Exception e) {
                System.err.println("Error setting window opacity: " + e.getMessage());
            }


            timeLabel = new JLabel("今日使用: 00:00:00", SwingConstants.CENTER);
            timeLabel.setFont(new Font("Arial", Font.BOLD, 16));
            timeLabel.setForeground(Color.WHITE);
            
            // Panel to hold the label and set background
            JPanel panel = new JPanel(new BorderLayout());
            panel.setBackground(new Color(0, 0, 0, 180)); // Semi-transparent black
            panel.setOpaque(true); // Panel itself is opaque, but its background color has alpha
            panel.add(timeLabel, BorderLayout.CENTER);
            window.setContentPane(panel);
            
            // If window.setOpacity is not effective, and background needs to be transparent:
            // window.setBackground(new Color(0,0,0,0)); // Make JWindow background transparent
            // panel.setOpaque(false); // And make panel transparent if its background is not the one we want

            window.setSize(200, 40);

            // Center on top of screen
            Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();
            window.setLocation((screenSize.width - window.getWidth()) / 2, 20); // 20px from top

            // Draggability
            MouseAdapter mouseAdapter = new MouseAdapter() {
                @Override
                public void mousePressed(MouseEvent e) {
                    initialClick = e.getPoint();
                }

                @Override
                public void mouseDragged(MouseEvent e) {
                    if (initialClick == null) return;
                    int thisX = window.getLocation().x;
                    int thisY = window.getLocation().y;

                    int xMoved = e.getX() - initialClick.x;
                    int yMoved = e.getY() - initialClick.y;

                    int newX = thisX + xMoved;
                    int newY = thisY + yMoved;
                    window.setLocation(newX, newY);
                }
            };
            window.addMouseListener(mouseAdapter);
            window.addMouseMotionListener(mouseAdapter);

            updateTimer = new Timer(1000, e -> updateDisplayTime());
            updateTimer.start();

            window.setVisible(true);
            System.out.println("Floating usage window displayed.");
        });
    }

    private void updateDisplayTime() {
        if (timeLabel != null && usageTracker != null) {
            long dailySeconds = usageTracker.getDailyUsageTime();
            timeLabel.setText("今日使用: " + UsageTracker.formatTime(dailySeconds));
        }
    }

    public void showWindow() {
        if (window != null) {
            SwingUtilities.invokeLater(() -> window.setVisible(true));
            if (updateTimer != null && !updateTimer.isRunning()) {
                updateTimer.start();
            }
            System.out.println("Floating window shown.");
        } else if (configManager.getBoolean("showFloatWindow", true)) {
            // Window was not initialized or was disposed, re-initialize
            initializeAndShow();
        }
    }

    public void hideWindow() {
        if (window != null && window.isVisible()) {
            SwingUtilities.invokeLater(() -> window.setVisible(false));
            // Optionally stop the timer when hidden to save resources,
            // but keep it running if you want time to be up-to-date when re-shown.
            // if (updateTimer != null && updateTimer.isRunning()) {
            //     updateTimer.stop();
            // }
            System.out.println("Floating window hidden.");
        }
    }
    
    public void disposeWindow() {
        SwingUtilities.invokeLater(() -> {
            if (updateTimer != null) {
                updateTimer.stop();
            }
            if (window != null) {
                window.dispose();
                window = null; // Allow for re-initialization
            }
            System.out.println("Floating window disposed.");
        });
    }

    // For testing purposes
    public String getCurrentDisplayTime() {
        if (timeLabel != null) {
            return timeLabel.getText();
        }
        return null;
    }

    public JWindow getWindow() {
        return window;
    }
}
