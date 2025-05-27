package com.example.config;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Comparator;
import java.util.Properties;
import java.io.FileInputStream;

import static org.junit.Assert.*;

public class ConfigManagerTest {

    private static final String TEST_CONFIG_DIR = "test_config_dir";
    private static final String TEST_CONFIG_FILE_NAME = "config.properties";
    private ConfigManager configManager;
    private Path testConfigPath;

    @Before
    public void setUp() throws IOException {
        testConfigPath = Paths.get(TEST_CONFIG_DIR);
        // Clean up before each test
        if (Files.exists(testConfigPath)) {
            Files.walk(testConfigPath)
                    .sorted(Comparator.reverseOrder())
                    .map(Path::toFile)
                    .forEach(File::delete);
        }
        Files.createDirectories(testConfigPath);
        configManager = new ConfigManager(TEST_CONFIG_DIR);
    }

    @After
    public void tearDown() throws IOException {
        // Clean up after each test
        if (Files.exists(testConfigPath)) {
            Files.walk(testConfigPath)
                    .sorted(Comparator.reverseOrder())
                    .map(Path::toFile)
                    .forEach(File::delete);
        }
    }

    @Test
    public void testDefaultConfigCreation() {
        File configFile = new File(TEST_CONFIG_DIR, TEST_CONFIG_FILE_NAME);
        assertTrue("Config file should be created", configFile.exists());

        // Verify some default properties
        assertEquals("YOUR_BOT_TOKEN", configManager.getString("botToken", ""));
        assertEquals(1, configManager.getInt("screenshotInterval", 0));
        assertTrue(configManager.getBoolean("showFloatWindow", false));
        assertEquals("admin", configManager.getString("adminPassword", ""));
    }

    @Test
    public void testGetString() {
        assertEquals("YOUR_BOT_TOKEN", configManager.getString("botToken", "default"));
        assertEquals("default_value", configManager.getString("nonExistentKey", "default_value"));
    }

    @Test
    public void testGetInt() {
        assertEquals(21, configManager.getInt("firstReminderHour", 0));
        assertEquals(123, configManager.getInt("nonExistentIntKey", 123));
        // Test with a non-integer value in properties (should return default)
        configManager.setSetting("testIntMalformed", "not_an_int");
        configManager.saveConfig(); // need to save to see the effect in this test structure
        ConfigManager newManager = new ConfigManager(TEST_CONFIG_DIR); // Re-load
        assertEquals(500, newManager.getInt("testIntMalformed", 500));

    }

    @Test
    public void testGetBoolean() {
        assertTrue(configManager.getBoolean("enableRestReminder", false));
        assertFalse(configManager.getBoolean("nonExistentBooleanKey", false));
        assertTrue(configManager.getBoolean("nonExistentBooleanKeyTrue", true));
    }

    @Test
    public void testSetAndSaveSetting() throws IOException {
        String newBotToken = "NEW_TEST_TOKEN";
        configManager.setSetting("botToken", newBotToken);
        configManager.saveConfig();

        // Verify by loading properties file directly
        Properties props = new Properties();
        try (FileInputStream fis = new FileInputStream(new File(TEST_CONFIG_DIR, TEST_CONFIG_FILE_NAME))) {
            props.load(fis);
        }
        assertEquals(newBotToken, props.getProperty("botToken"));

        // Verify using a new ConfigManager instance
        ConfigManager newConfigManager = new ConfigManager(TEST_CONFIG_DIR);
        assertEquals(newBotToken, newConfigManager.getString("botToken", ""));
    }
    
    @Test
    public void testLoadExistingConfig() throws IOException {
        // Create a config file manually
        Properties props = new Properties();
        props.setProperty("customKey", "customValue");
        props.setProperty("customInt", "12345");
        File configFile = new File(TEST_CONFIG_DIR, TEST_CONFIG_FILE_NAME);
        try (FileOutputStream fos = new FileOutputStream(configFile)) {
            props.store(fos, "Test custom config");
        }

        ConfigManager newManager = new ConfigManager(TEST_CONFIG_DIR);
        assertEquals("customValue", newManager.getString("customKey", ""));
        assertEquals(12345, newManager.getInt("customInt", 0));
        // Default values should still be accessible if not overridden
        assertEquals("YOUR_BOT_TOKEN", newManager.getString("botToken", ""));
    }


    @Test
    public void testErrorHandlingForMalformedInt() {
        configManager.setSetting("malformedInt", "not-a-number");
        configManager.saveConfig();
        // Create new instance to ensure it loads from file
        ConfigManager newManager = new ConfigManager(TEST_CONFIG_DIR);
        assertEquals(999, newManager.getInt("malformedInt", 999));
    }
}
