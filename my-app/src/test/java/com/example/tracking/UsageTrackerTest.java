package com.example.tracking;

import com.example.config.ConfigManager;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Comparator;
import java.util.Properties;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;

public class UsageTrackerTest {

    private static final String TEST_CONFIG_DIR = "test_tracker_config_dir";
    private static final String TEST_STATS_FILE_NAME = "test_usage_stats.json";
    private static final Path TEST_CONFIG_PATH = Paths.get(TEST_CONFIG_DIR);
    private static final Path TEST_STATS_FILE_PATH = TEST_CONFIG_PATH.resolve(TEST_STATS_FILE_NAME);

    private ConfigManager mockConfigManager;
    private UsageTracker usageTracker;
    private Gson gson;

    @Before
    public void setUp() throws IOException {
        // Clean up and create directories
        if (Files.exists(TEST_CONFIG_PATH)) {
            Files.walk(TEST_CONFIG_PATH)
                    .sorted(Comparator.reverseOrder())
                    .map(Path::toFile)
                    .forEach(File::delete);
        }
        Files.createDirectories(TEST_CONFIG_PATH);

        mockConfigManager = mock(ConfigManager.class);
        // Provide a valid directory for usageStatsFile via the mock
        // Ensure the file path is within the test-specific directory
        when(mockConfigManager.getString(eq("usageStatsFile"), anyString())).thenReturn(TEST_STATS_FILE_PATH.toString());
        when(mockConfigManager.getInt(eq("saveStatsIntervalSeconds"), anyInt())).thenReturn(60); // Default save interval

        usageTracker = new UsageTracker(mockConfigManager);
        gson = new GsonBuilder().setPrettyPrinting().create();
    }

    @After
    public void tearDown() throws IOException {
        if (usageTracker != null && usageTracker.isRunning()) {
            usageTracker.stopTracking();
        }
        // Clean up test files and directory
         if (Files.exists(TEST_CONFIG_PATH)) {
            Files.walk(TEST_CONFIG_PATH)
                    .sorted(Comparator.reverseOrder())
                    .map(Path::toFile)
                    .forEach(File::delete);
        }
    }

    private void writeStatsFile(String date, long dailyTime) throws IOException {
        UsageTracker.UsageStats stats = new UsageTracker.UsageStats(date, dailyTime);
        try (FileWriter writer = new FileWriter(TEST_STATS_FILE_PATH.toFile())) {
            gson.toJson(stats, writer);
        }
    }

    @Test
    public void testLoadUsageStats_newDay() throws IOException {
        writeStatsFile(LocalDate.now().minusDays(1).format(DateTimeFormatter.ISO_DATE), 1000);
        usageTracker.loadUsageStats(); // Reload explicitly
        assertEquals(0, usageTracker.getDailyUsageTime());
        assertEquals(0, usageTracker.getContinuousUsageTime());
    }

    @Test
    public void testLoadUsageStats_sameDay() throws IOException {
        long expectedTime = 12345;
        writeStatsFile(LocalDate.now().format(DateTimeFormatter.ISO_DATE), expectedTime);
        usageTracker.loadUsageStats(); // Reload explicitly
        assertEquals(expectedTime, usageTracker.getDailyUsageTime());
        assertEquals(0, usageTracker.getContinuousUsageTime()); // Continuous should always reset
    }

    @Test
    public void testLoadUsageStats_fileNotFound() {
        // Ensure file does not exist
        if(TEST_STATS_FILE_PATH.toFile().exists()) TEST_STATS_FILE_PATH.toFile().delete();
        
        usageTracker.loadUsageStats(); // Should not throw error, should init to 0
        assertEquals(0, usageTracker.getDailyUsageTime());
        assertEquals(0, usageTracker.getContinuousUsageTime());
    }
    
    @Test
    public void testLoadUsageStats_malformedJson() throws IOException {
        try (FileWriter writer = new FileWriter(TEST_STATS_FILE_PATH.toFile())) {
            writer.write("this is not json");
        }
        usageTracker.loadUsageStats();
        assertEquals(0, usageTracker.getDailyUsageTime());
    }


    @Test
    public void testSaveUsageStats() throws IOException {
        usageTracker.startTracking(); // Start to initialize lastCheckTime
        // Simulate some time passing
        usageTracker.updateUsageTime(); // Call once to establish a baseline
        try { Thread.sleep(1100); } catch (InterruptedException e) { fail("Sleep interrupted"); }
        usageTracker.updateUsageTime();
        usageTracker.stopTracking(); // This will call saveUsageStats

        File statsFile = TEST_STATS_FILE_PATH.toFile();
        assertTrue("Stats file should exist after save", statsFile.exists());

        try (FileReader reader = new FileReader(statsFile)) {
            UsageTracker.UsageStats stats = gson.fromJson(reader, UsageTracker.UsageStats.class);
            assertNotNull(stats);
            assertEquals(LocalDate.now().format(DateTimeFormatter.ISO_DATE), stats.today_date);
            assertTrue("Daily usage time should be greater than 0 after tracking", stats.daily_usage_time > 0);
            assertEquals(usageTracker.getDailyUsageTime(), stats.daily_usage_time);
        }
    }

    @Test
    public void testUpdateUsageTime() throws InterruptedException {
        usageTracker.startTracking();
        assertEquals(0, usageTracker.getDailyUsageTime());
        assertEquals(0, usageTracker.getContinuousUsageTime());

        Thread.sleep(1050); // Sleep for just over a second
        // updateUsageTime is called by the scheduler, but we can also call it manually
        // to observe its effect if scheduler is too slow for test precision or not trusted in test
        // For this test, rely on the internal scheduler.
        
        // Wait for a couple of scheduler ticks
        Thread.sleep(2050); 

        long dailyUsage = usageTracker.getDailyUsageTime();
        long continuousUsage = usageTracker.getContinuousUsageTime();

        assertTrue("Daily usage should increase", dailyUsage >= 2 && dailyUsage <=4 ); // Allow some leeway for thread scheduling
        assertTrue("Continuous usage should increase", continuousUsage >= 2 && continuousUsage <=4);

        usageTracker.stopTracking();
    }


    @Test
    public void testResetContinuousUsageTime() throws InterruptedException {
        usageTracker.startTracking();
        Thread.sleep(1050); // Let some time pass
        usageTracker.updateUsageTime(); // Update manually or wait for scheduler
         Thread.sleep(1050); 
        assertTrue(usageTracker.getContinuousUsageTime() > 0);
        usageTracker.resetContinuousUsageTime();
        assertEquals(0, usageTracker.getContinuousUsageTime());
        usageTracker.stopTracking();
    }

    @Test
    public void testFormatTime() {
        assertEquals("00:00:00", UsageTracker.formatTime(0));
        assertEquals("00:00:01", UsageTracker.formatTime(1));
        assertEquals("00:01:00", UsageTracker.formatTime(60));
        assertEquals("01:00:00", UsageTracker.formatTime(3600));
        assertEquals("01:01:01", UsageTracker.formatTime(3661));
        assertEquals("23:59:59", UsageTracker.formatTime(86399));
    }
    
    @Test
    public void testTrackingLifecycle() throws InterruptedException {
        assertFalse(usageTracker.isRunning());
        usageTracker.startTracking();
        assertTrue(usageTracker.isRunning());
        Thread.sleep(500); // Let it run for a bit
        long usageAfterStart = usageTracker.getDailyUsageTime();
        // Depending on timing, usage might be 0 or 1 second.
        // More reliably, check if it increases after more time.
        Thread.sleep(1000);
        assertTrue("Usage should increase after time", usageTracker.getDailyUsageTime() > usageAfterStart || usageTracker.getDailyUsageTime() >=1);

        usageTracker.stopTracking();
        assertFalse(usageTracker.isRunning());
        long finalUsage = usageTracker.getDailyUsageTime();
        Thread.sleep(1000); // Wait to ensure no more updates happen
        assertEquals("Usage should not change after stopping", finalUsage, usageTracker.getDailyUsageTime());
    }

    @Test
    public void testPeriodicSave() throws InterruptedException, IOException {
         // Mock config to save very frequently for testing purposes
        when(mockConfigManager.getInt(eq("saveStatsIntervalSeconds"), anyInt())).thenReturn(1); // Save every 1 second
        usageTracker = new UsageTracker(mockConfigManager); // Re-initialize with new mock config
        
        usageTracker.startTracking();
        Thread.sleep(1500); // Wait for more than one save interval
        usageTracker.stopTracking(); // This also saves

        File statsFile = TEST_STATS_FILE_PATH.toFile();
        assertTrue("Stats file should exist", statsFile.exists());
        
        try (FileReader reader = new FileReader(statsFile)) {
            UsageTracker.UsageStats stats = gson.fromJson(reader, UsageTracker.UsageStats.class);
            assertNotNull(stats);
            // Daily usage should be around 1 or 2 seconds
            assertTrue("Daily usage time should be around 1-2 seconds", stats.daily_usage_time >= 1 && stats.daily_usage_time <=2);
        }
    }
}
