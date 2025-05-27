package com.example.ui;

import com.example.config.ConfigManager;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Properties;

public class SettingsUI {

    private final ConfigManager configManager;
    private JFrame settingsFrame;
    private Map<String, JTextField> settingFields; // Using JTextField for all, JPasswordField handled separately for display

    public SettingsUI(ConfigManager configManager) {
        this.configManager = configManager;
        this.settingFields = new LinkedHashMap<>(); // Preserve order of insertion
    }

    private boolean promptForPassword() {
        JPanel panel = new JPanel();
        JLabel label = new JLabel("Enter admin password:");
        JPasswordField passwordField = new JPasswordField(20);
        panel.add(label);
        panel.add(passwordField);
        String[] options = new String[]{"OK", "Cancel"};
        int option = JOptionPane.showOptionDialog(null, panel, "Admin Access Required",
                JOptionPane.NO_OPTION, JOptionPane.PLAIN_MESSAGE,
                null, options, options[0]);

        if (option == 0) { // OK
            String enteredPassword = new String(passwordField.getPassword());
            String storedPassword = configManager.getString("adminPassword", "admin");
            if (enteredPassword.equals(storedPassword)) {
                return true;
            } else {
                JOptionPane.showMessageDialog(null, "Incorrect password.", "Access Denied", JOptionPane.ERROR_MESSAGE);
                return false;
            }
        }
        return false; // Cancel or closed dialog
    }

    public void displaySettings() {
        if (!promptForPassword()) {
            return;
        }

        if (settingsFrame != null && settingsFrame.isVisible()) {
            settingsFrame.toFront();
            return;
        }

        settingsFrame = new JFrame("Application Settings");
        settingsFrame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        settingsFrame.setSize(500, 600); // Adjusted size for more fields
        settingsFrame.setLayout(new BorderLayout());
        settingsFrame.setLocationRelativeTo(null);

        JPanel fieldsPanel = new JPanel();
        // Use GridBagLayout for better control over component placement
        fieldsPanel.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.gridx = 0;
        gbc.gridy = 0;
        gbc.insets = new Insets(5, 5, 5, 5); // Padding
        gbc.anchor = GridBagConstraints.WEST;

        settingFields.clear(); // Clear previous fields if any

        Properties allProps = configManager.getAllSettings();
        // Maintain a consistent order if possible, or define a specific order
        // For now, iterating through properties as they are (order might not be guaranteed from Properties)
        // A predefined list of keys would be better for fixed order.
        
        // Predefined order for critical settings, then others
        String[] orderedKeys = {
            "dataFolder", "botToken", "chatId", "proxy", "screenshotInterval", 
            "usageStatsFile", "showFloatWindow", "enableRestReminder", 
            "firstReminderHour", "shutdownPlanHour", "shutdownPlanMinute", "shutdownDelayMinutes",
            "reminderIntervalSeconds", "continuousUsageThreshold", "forcedRestDuration",
            "forcedShutdownHour", "adminPassword" 
        };

        for (String key : orderedKeys) {
            if (!allProps.containsKey(key)) continue; // Skip if key not in current props
            
            JLabel label = new JLabel(key + ":");
            gbc.gridx = 0;
            gbc.fill = GridBagConstraints.NONE;
            fieldsPanel.add(label, gbc);

            gbc.gridx = 1;
            gbc.fill = GridBagConstraints.HORIZONTAL;
            gbc.weightx = 1.0; // Allow text field to expand

            JTextField field;
            if ("adminPassword".equals(key)) {
                field = new JPasswordField(allProps.getProperty(key, ""));
            } else {
                field = new JTextField(allProps.getProperty(key, ""));
            }
            settingFields.put(key, field);
            fieldsPanel.add(field, gbc);
            gbc.gridy++;
        }
        
        // Add any remaining properties not in orderedKeys (optional, for robustness)
        allProps.forEach((k, v) -> {
            String key = (String) k;
            if (!java.util.Arrays.asList(orderedKeys).contains(key)) {
                 JLabel label = new JLabel(key + ":");
                gbc.gridx = 0;
                gbc.fill = GridBagConstraints.NONE;
                fieldsPanel.add(label, gbc);

                gbc.gridx = 1;
                gbc.fill = GridBagConstraints.HORIZONTAL;
                gbc.weightx = 1.0;
                JTextField field = new JTextField((String) v);
                settingFields.put(key, field);
                fieldsPanel.add(field, gbc);
                gbc.gridy++;
            }
        });


        JScrollPane scrollPane = new JScrollPane(fieldsPanel);
        settingsFrame.add(scrollPane, BorderLayout.CENTER);

        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        JButton saveButton = new JButton("Save");
        saveButton.addActionListener(this::saveSettingsAction);
        buttonPanel.add(saveButton);

        JButton cancelButton = new JButton("Close");
        cancelButton.addActionListener(e -> settingsFrame.dispose());
        buttonPanel.add(cancelButton);
        
        JButton changePasswordButton = new JButton("Change Admin Password");
        changePasswordButton.addActionListener(e -> displayChangePasswordDialog(settingsFrame)); // Pass parent frame
        buttonPanel.add(changePasswordButton);


        settingsFrame.add(buttonPanel, BorderLayout.SOUTH);
        settingsFrame.setVisible(true);
    }

    private void saveSettingsAction(ActionEvent e) {
        settingFields.forEach((key, field) -> {
            String value;
            if (field instanceof JPasswordField) {
                value = new String(((JPasswordField) field).getPassword());
            } else {
                value = field.getText();
            }
            configManager.setSetting(key, value);
        });
        configManager.saveConfig();
        JOptionPane.showMessageDialog(settingsFrame, "Settings saved successfully.", "Success", JOptionPane.INFORMATION_MESSAGE);
        settingsFrame.dispose();
    }

    public void displayChangePasswordDialog(Component parentComponent) {
        // Step 1: Prompt for current admin password
        JPanel currentPasswordPanel = new JPanel();
        currentPasswordPanel.add(new JLabel("Enter current admin password:"));
        JPasswordField currentPasswordField = new JPasswordField(20);
        currentPasswordPanel.add(currentPasswordField);

        int currentPwdOption = JOptionPane.showConfirmDialog(parentComponent, currentPasswordPanel,
                "Verify Current Password", JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE);

        if (currentPwdOption != JOptionPane.OK_OPTION) {
            return; // User cancelled
        }

        String enteredCurrentPassword = new String(currentPasswordField.getPassword());
        String storedAdminPassword = configManager.getString("adminPassword", "admin");

        if (!enteredCurrentPassword.equals(storedAdminPassword)) {
            JOptionPane.showMessageDialog(parentComponent, "Incorrect current password.", "Verification Failed", JOptionPane.ERROR_MESSAGE);
            return;
        }

        // Step 2: Prompt for new password and confirmation
        JPanel newPasswordPanel = new JPanel(new GridLayout(2, 2));
        newPasswordPanel.add(new JLabel("Enter new password:"));
        JPasswordField newPasswordField = new JPasswordField(20);
        newPasswordPanel.add(newPasswordField);
        newPasswordPanel.add(new JLabel("Confirm new password:"));
        JPasswordField confirmPasswordField = new JPasswordField(20);
        newPasswordPanel.add(confirmPasswordField);

        int newPwdOption = JOptionPane.showConfirmDialog(parentComponent, newPasswordPanel,
                "Set New Password", JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE);

        if (newPwdOption != JOptionPane.OK_OPTION) {
            return; // User cancelled
        }

        String newPassword = new String(newPasswordField.getPassword());
        String confirmPassword = new String(confirmPasswordField.getPassword());

        if (newPassword.isEmpty()) {
            JOptionPane.showMessageDialog(parentComponent, "New password cannot be empty.", "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }

        if (!newPassword.equals(confirmPassword)) {
            JOptionPane.showMessageDialog(parentComponent, "New passwords do not match.", "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }

        // Step 3: Update and save
        configManager.setSetting("adminPassword", newPassword);
        configManager.saveConfig();
        
        // Update the JPasswordField in the main settings window if it's open and showing adminPassword
        if (settingFields.containsKey("adminPassword")) {
            settingFields.get("adminPassword").setText(newPassword); // JPasswordField's setText works
        }

        JOptionPane.showMessageDialog(parentComponent, "Admin password changed successfully.", "Success", JOptionPane.INFORMATION_MESSAGE);
    }
}
