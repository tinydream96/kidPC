package com.example.config;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Properties;

public class ConfigManager {

    private static final String CONFIG_FILE_NAME = "config.properties";
    private Properties properties;
    private String configFilePath;

    public ConfigManager() {
        this("."); // Default to current directory
    }

    public ConfigManager(String configDir) {
        this.configFilePath = configDir + File.separator + CONFIG_FILE_NAME;
        this.properties = new Properties();
        loadConfig();
    }

    private void loadConfig() {
        File configFile = new File(configFilePath);
        if (configFile.exists()) {
            try (InputStream input = new FileInputStream(configFile)) {
                properties.load(input);
            } catch (IOException e) {
                System.err.println("Error loading configuration file: " + e.getMessage());
                // Consider creating default if loading fails critically
                createDefaultConfig();
            }
        } else {
            System.out.println("Configuration file not found. Creating default configuration.");
            createDefaultConfig();
        }
    }

    private void createDefaultConfig() {
        properties.setProperty("dataFolder", ".//screenshots");
        properties.setProperty("botToken", "YOUR_BOT_TOKEN");
        properties.setProperty("chatId", "YOUR_CHAT_ID");
        properties.setProperty("proxy", "");
        properties.setProperty("screenshotInterval", "1");
        properties.setProperty("usageStatsFile", ".//usage_stats.json");
        properties.setProperty("showFloatWindow", "true");
        properties.setProperty("enableRestReminder", "true");
        properties.setProperty("firstReminderHour", "21");
        properties.setProperty("shutdownPlanHour", "21");
        properties.setProperty("shutdownPlanMinute", "30");
        properties.setProperty("shutdownDelayMinutes", "5");
        properties.setProperty("reminderIntervalSeconds", "300");
        properties.setProperty("continuousUsageThreshold", "10");
        properties.setProperty("forcedRestDuration", "1");
        properties.setProperty("forcedShutdownHour", "22");
        properties.setProperty("adminPassword", "admin");
        saveConfig();
    }

    public Properties getAllSettings() {
        // Return a copy to prevent external modification of the internal properties object
        Properties copy = new Properties();
        copy.putAll(this.properties);
        return copy;
    }

    public String getString(String key, String defaultValue) {
        return properties.getProperty(key, defaultValue);
    }

    public int getInt(String key, int defaultValue) {
        try {
            return Integer.parseInt(properties.getProperty(key));
        } catch (NumberFormatException | NullPointerException e) {
            System.err.println("Error parsing int for key '" + key + "'. Using default value: " + defaultValue);
            return defaultValue;
        }
    }

    public boolean getBoolean(String key, boolean defaultValue) {
        String value = properties.getProperty(key);
        if (value == null) {
            return defaultValue;
        }
        return Boolean.parseBoolean(value);
    }

    public void setSetting(String key, String value) {
        properties.setProperty(key, value);
    }

    public void saveConfig() {
        File configFile = new File(configFilePath);
        try (OutputStream output = new FileOutputStream(configFile)) {
            properties.store(output, "Application Configuration");
            System.out.println("Configuration saved to " + configFile.getAbsolutePath());
        } catch (IOException e) {
            System.err.println("Error saving configuration file: " + e.getMessage());
        }
    }

    // Main method for testing
    public static void main(String[] args) {
        ConfigManager configManager = new ConfigManager("my-app-config"); // test in a sub-directory
        System.out.println("botToken: " + configManager.getString("botToken", "default_token"));
        configManager.setSetting("botToken", "NEW_TOKEN_123");
        System.out.println("botToken after set: " + configManager.getString("botToken", "default_token"));
        configManager.saveConfig();
        System.out.println("Screenshot Interval: " + configManager.getInt("screenshotInterval", 60));
        System.out.println("Show Float Window: " + configManager.getBoolean("showFloatWindow", false));

        // Test non-existent key
        System.out.println("NonExistentKey (String): " + configManager.getString("nonExistentKey", "defaultString"));
        System.out.println("NonExistentKey (int): " + configManager.getInt("nonExistentKeyInt", 12345));
        System.out.println("NonExistentKey (boolean): " + configManager.getBoolean("nonExistentKeyBool", true));

        // Test creating a new config if one doesn't exist
        File testConfigFile = new File("my-app-config" + File.separator + CONFIG_FILE_NAME);
        if(testConfigFile.exists()){
            if(testConfigFile.delete()){
                 System.out.println("Deleted test config to recreate.");
                 ConfigManager newManager = new ConfigManager("my-app-config");
                 System.out.println("New botToken: " + newManager.getString("botToken", "default_token"));
            }
        }
    }
}
