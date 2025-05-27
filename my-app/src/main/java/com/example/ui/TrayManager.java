package com.example.ui;

import com.example.App; // Assuming App class will have methods to call

import java.awt.*;
import java.awt.event.ActionListener;
import java.awt.image.BufferedImage; // Added import
import java.net.URL;
import javax.swing.ImageIcon;

public class TrayManager {

    private final App app; // Reference to the main application class
    private TrayIcon trayIcon;

    public TrayManager(App app) {
        this.app = app;
    }

    public void setupTrayIcon() { // Corrected method name
        if (!SystemTray.isSupported()) {
            System.err.println("SystemTray is not supported. Skipping tray icon setup.");
            return;
        }

        SystemTray systemTray = SystemTray.getSystemTray();
        
        // Load icon image
        // Using ClassLoader to get resource from classpath (e.g., src/main/resources)
        URL imageUrl = getClass().getClassLoader().getResource("icon.png");
        Image image;
        if (imageUrl != null) {
            image = new ImageIcon(imageUrl).getImage();
        } else {
            // Fallback: Create a simple default image if icon.png is not found
            System.err.println("icon.png not found in resources. Using a default image.");
            image = new BufferedImage(16, 16, BufferedImage.TYPE_INT_RGB); // Placeholder
            Graphics g = image.getGraphics();
            g.setColor(Color.BLUE);
            g.fillRect(0, 0, 16, 16);
            g.dispose();
        }


        PopupMenu trayPopupMenu = new PopupMenu();

        // Menu Item: Open Settings
        MenuItem settingsItem = new MenuItem("Open Settings");
        settingsItem.addActionListener(e -> app.showSettingsWindow());
        trayPopupMenu.add(settingsItem);

        // Menu Item: Change Password
        MenuItem changePasswordItem = new MenuItem("Change Password");
        changePasswordItem.addActionListener(e -> app.showChangePasswordDialog());
        trayPopupMenu.add(changePasswordItem);
        
        trayPopupMenu.addSeparator();

        // Menu Item: Exit
        MenuItem exitItem = new MenuItem("Exit");
        exitItem.addActionListener(e -> app.exitApplication());
        trayPopupMenu.add(exitItem);

        trayIcon = new TrayIcon(image, "REST Reminder", trayPopupMenu);
        trayIcon.setImageAutoSize(true);

        try {
            systemTray.add(trayIcon);
            trayIcon.displayMessage("REST Reminder", "Application Started", TrayIcon.MessageType.INFO);
            System.out.println("Tray icon added successfully.");
        } catch (AWTException e) {
            System.err.println("TrayIcon could not be added: " + e.getMessage());
        }
    }
    
    public void removeTrayIcon() {
        if (SystemTray.isSupported() && trayIcon != null) {
            SystemTray.getSystemTray().remove(trayIcon);
            System.out.println("Tray icon removed.");
        }
    }
}
