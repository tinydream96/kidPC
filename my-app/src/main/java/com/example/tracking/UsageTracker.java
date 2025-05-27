package com.example.tracking;

import com.example.config.ConfigManager;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonSyntaxException;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class UsageTracker {

    private final ConfigManager configManager;
    private long dailyUsageTime; // in seconds
    private long continuousUsageTime; // in seconds
    private long lastCheckTime;
    private volatile boolean running;
    private ScheduledExecutorService scheduler;
    private final Gson gson;
    private final String usageStatsFilePath;

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ISO_DATE;

    static class UsageStats {
        String today_date;
        long daily_usage_time;

        UsageStats(String date, long time) {
            this.today_date = date;
            this.daily_usage_time = time;
        }
    }

    public UsageTracker(ConfigManager configManager) {
        this.configManager = configManager;
        this.gson = new GsonBuilder().setPrettyPrinting().create();
        // Correctly resolve the file path relative to the config file's directory or a base path
        String configFileDir = new File(configManager.getString("usageStatsFile","usage_stats.json")).getParent();
        if (configFileDir == null) {
            configFileDir = "."; // Default to current directory if no parent is specified
        }
        this.usageStatsFilePath = configFileDir + File.separator + new File(configManager.getString("usageStatsFile", "usage_stats.json")).getName();
        
        loadUsageStats();
        this.lastCheckTime = System.currentTimeMillis();
    }

    public void loadUsageStats() {
        File statsFile = new File(usageStatsFilePath);
        if (statsFile.exists()) {
            try (FileReader reader = new FileReader(statsFile)) {
                UsageStats stats = gson.fromJson(reader, UsageStats.class);
                if (stats != null && LocalDate.now().format(DATE_FORMATTER).equals(stats.today_date)) {
                    this.dailyUsageTime = stats.daily_usage_time;
                } else {
                    this.dailyUsageTime = 0; // New day or malformed date
                }
            } catch (IOException | JsonSyntaxException e) {
                System.err.println("Error loading usage stats: " + e.getMessage());
                this.dailyUsageTime = 0;
            }
        } else {
            this.dailyUsageTime = 0; // No file exists
        }
        this.continuousUsageTime = 0; // Always reset continuous usage on load/reload
        System.out.println("Loaded usage stats. Daily: " + dailyUsageTime + "s, Continuous: " + continuousUsageTime + "s");
    }

    public void saveUsageStats() {
        UsageStats stats = new UsageStats(LocalDate.now().format(DATE_FORMATTER), dailyUsageTime);
        File statsFile = new File(usageStatsFilePath);
        try {
            // Ensure parent directory exists
            File parentDir = statsFile.getParentFile();
            if (parentDir != null && !parentDir.exists()) {
                if (!parentDir.mkdirs()) {
                    System.err.println("Could not create parent directories for usage stats file: " + usageStatsFilePath);
                    return;
                }
            }
            try (FileWriter writer = new FileWriter(statsFile)) {
                gson.toJson(stats, writer);
            }
        } catch (IOException e) {
            System.err.println("Error saving usage stats: " + e.getMessage());
        }
    }

    public void updateUsageTime() {
        if (!running) return;

        long currentTime = System.currentTimeMillis();
        long elapsedMillis = currentTime - lastCheckTime;
        if (elapsedMillis > 0) {
            long elapsedSeconds = elapsedMillis / 1000;
            dailyUsageTime += elapsedSeconds;
            continuousUsageTime += elapsedSeconds;
        }
        lastCheckTime = currentTime;
    }

    public void startTracking() {
        running = true;
        lastCheckTime = System.currentTimeMillis(); // Reset lastCheckTime when starting
        scheduler = Executors.newSingleThreadScheduledExecutor();

        // Update usage time every second
        scheduler.scheduleAtFixedRate(this::updateUsageTime, 0, 1, TimeUnit.SECONDS);

        // Save stats periodically (e.g., every minute)
        int saveInterval = configManager.getInt("saveStatsIntervalSeconds", 60); // New config option
        scheduler.scheduleAtFixedRate(this::saveUsageStats, saveInterval, saveInterval, TimeUnit.SECONDS);
        System.out.println("Usage tracking started.");
    }

    public void stopTracking() {
        running = false;
        if (scheduler != null && !scheduler.isShutdown()) {
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
        saveUsageStats(); // Final save
        System.out.println("Usage tracking stopped. Final stats saved.");
    }

    public long getDailyUsageTime() {
        return dailyUsageTime;
    }

    public long getContinuousUsageTime() {
        return continuousUsageTime;
    }

    public void resetContinuousUsageTime() {
        this.continuousUsageTime = 0;
        System.out.println("Continuous usage time reset.");
    }

    public static String formatTime(long totalSeconds) {
        long hours = totalSeconds / 3600;
        long minutes = (totalSeconds % 3600) / 60;
        long seconds = totalSeconds % 60;
        return String.format("%02d:%02d:%02d", hours, minutes, seconds);
    }

    public boolean isRunning() {
        return running;
    }
}
