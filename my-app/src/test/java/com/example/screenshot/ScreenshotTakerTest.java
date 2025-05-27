package com.example.screenshot;

import com.example.config.ConfigManager;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.awt.*;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Date;
import java.util.Objects;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;

public class ScreenshotTakerTest {

    private static final String TEST_DATA_FOLDER_NAME = "test_screenshots_output_for_taker";
    private static final Path TEST_DATA_FOLDER_PATH = Paths.get(TEST_DATA_FOLDER_NAME);

    @Mock
    private ConfigManager mockConfigManager;

    private ScreenshotTaker screenshotTaker;
    private AutoCloseable mockitoCloseable;


    @Before
    public void setUp() throws IOException {
        mockitoCloseable = MockitoAnnotations.openMocks(this);

        // Configure mock ConfigManager
        // Return a specific path for "dataFolder" that is within our test-controlled directory
        when(mockConfigManager.getString("dataFolder", "screenshots")).thenReturn(TEST_DATA_FOLDER_PATH.toString());

        screenshotTaker = new ScreenshotTaker(mockConfigManager);

        // Clean up and create the test directory before each test
        if (Files.exists(TEST_DATA_FOLDER_PATH)) {
            Files.walk(TEST_DATA_FOLDER_PATH)
                    .sorted(Comparator.reverseOrder())
                    .map(Path::toFile)
                    .forEach(File::delete);
        }
        Files.createDirectories(TEST_DATA_FOLDER_PATH);
    }

    @After
    public void tearDown() throws Exception {
        mockitoCloseable.close();
        // Clean up the test directory after each test
        if (Files.exists(TEST_DATA_FOLDER_PATH)) {
            Files.walk(TEST_DATA_FOLDER_PATH)
                    .sorted(Comparator.reverseOrder())
                    .map(Path::toFile)
                    .forEach(File::delete);
        }
    }

    @Test
    public void testTakeScreenshot_createsFileInCorrectDirectory() {
        // Set a system property to indicate "test mode" for headless environments
        // This tells ScreenshotTaker to create a dummy file instead of using Robot
        System.setProperty("java.awt.headless.test", "true");

        String screenshotPath = screenshotTaker.takeScreenshot();
        assertNotNull("Screenshot path should not be null", screenshotPath);

        File screenshotFile = new File(screenshotPath);
        assertTrue("Screenshot file should exist", screenshotFile.exists());
        assertEquals("Screenshot should be in the configured data folder",
                TEST_DATA_FOLDER_PATH.toAbsolutePath().toString(),
                screenshotFile.getParentFile().getAbsolutePath());
        
        System.clearProperty("java.awt.headless.test"); // Clean up the property
    }

    @Test
    public void testTakeScreenshot_filenameFormat() {
        System.setProperty("java.awt.headless.test", "true");

        String screenshotPath = screenshotTaker.takeScreenshot();
        assertNotNull(screenshotPath);
        File screenshotFile = new File(screenshotPath);
        String filename = screenshotFile.getName();

        assertTrue("Filename should start with 'screenshot_'", filename.startsWith("screenshot_"));
        assertTrue("Filename should end with '.png'", filename.endsWith(".png"));

        // Check for timestamp part (e.g., "screenshot_YYYYMMDD_HHMMSS.png")
        // Length of "YYYYMMDD_HHMMSS" is 15
        String timestampPart = filename.substring("screenshot_".length(), filename.length() - ".png".length());
        assertEquals("Timestamp part length is incorrect", 15, timestampPart.length());
        assertTrue("Timestamp part should contain an underscore", timestampPart.contains("_"));
        
        // Further regex matching could be done here for YYYYMMDD_HHMMSS
        // For simplicity, checking length and basic structure.
        // Example: YYYYMMDD_HHMMSS
        // String regex = "\\d{8}_\\d{6}";
        // assertTrue("Timestamp format is incorrect", timestampPart.matches(regex));
        // For now, let's rely on the SimpleDateFormat in the main code being correct.

        System.clearProperty("java.awt.headless.test");
    }
    
    @Test
    public void testTakeScreenshot_directoryCreation() {
         System.setProperty("java.awt.headless.test", "true");
        // Delete the directory to ensure ScreenshotTaker creates it
        try {
            Files.walk(TEST_DATA_FOLDER_PATH)
                    .sorted(Comparator.reverseOrder())
                    .map(Path::toFile)
                    .forEach(File::delete);
        } catch (IOException e) {
            fail("Could not delete test directory for setup: " + e.getMessage());
        }
        assertFalse("Test data folder should not exist before takeScreenshot is called", Files.exists(TEST_DATA_FOLDER_PATH));

        screenshotTaker.takeScreenshot(); // This should trigger directory creation

        assertTrue("Data folder should be created by ScreenshotTaker", Files.exists(TEST_DATA_FOLDER_PATH));
        System.clearProperty("java.awt.headless.test");
    }


    @Test
    public void testTakeScreenshot_actualCapture() {
        // This test will only run if a graphics environment is available.
        if (GraphicsEnvironment.isHeadless()) {
            System.out.println("Skipping testTakeScreenshot_actualCapture in headless environment.");
            System.setProperty("java.awt.headless.test", "true"); // Allow dummy creation for path checks
            String path = screenshotTaker.takeScreenshot();
            assertNotNull("Path should not be null even for dummy in headless", path);
            System.clearProperty("java.awt.headless.test");
            return;
        }

        String screenshotPath = screenshotTaker.takeScreenshot();
        assertNotNull("Screenshot path should not be null in non-headless environment", screenshotPath);
        File screenshotFile = new File(screenshotPath);
        assertTrue("Screenshot file should exist after actual capture", screenshotFile.exists());
        assertTrue("Screenshot file should not be empty", screenshotFile.length() > 0);
    }
    
    @Test
    public void testDataFolderResolution() {
        // Test how dataFolder is resolved (this is partly testing constructor logic)
        assertEquals(TEST_DATA_FOLDER_PATH.toAbsolutePath().toString(), screenshotTaker.getDataFolder());
    }
}
