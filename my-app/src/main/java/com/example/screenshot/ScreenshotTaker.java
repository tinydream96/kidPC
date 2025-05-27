package com.example.screenshot;

import com.example.config.ConfigManager;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;

public class ScreenshotTaker {

    private final ConfigManager configManager;
    private final String dataFolder;

    public ScreenshotTaker(ConfigManager configManager) {
        this.configManager = configManager;
        // Resolve dataFolder path relative to the config file's location or a base path.
        // For simplicity, assuming configManager.getString("dataFolder", ...) returns a usable path.
        String configuredFolder = this.configManager.getString("dataFolder", "screenshots");
        
        File folder = new File(configuredFolder);
        if (!folder.isAbsolute()) {
            // If not absolute, make it relative to the application's working directory or a predefined base.
            // For this example, let's assume it's relative to the working directory.
            this.dataFolder = folder.getAbsolutePath();
        } else {
            this.dataFolder = configuredFolder;
        }
    }

    public String takeScreenshot() {
        File folder = new File(dataFolder);
        if (!folder.exists()) {
            if (!folder.mkdirs()) {
                System.err.println("Failed to create data folder: " + dataFolder);
                return null;
            }
        }

        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd_HHmmss");
        String timestamp = sdf.format(new Date());
        String filename = "screenshot_" + timestamp + ".png";
        File screenshotFile = new File(dataFolder, filename);

        try {
            if (GraphicsEnvironment.isHeadless()) {
                System.err.println("Cannot take screenshot in headless environment.");
                // Create a dummy file for testing purposes in headless mode
                if (System.getProperty("java.awt.headless.test") != null) {
                    try {
                        // Create a small dummy image
                        BufferedImage dummyImage = new BufferedImage(100, 100, BufferedImage.TYPE_INT_RGB);
                        Graphics2D g2d = dummyImage.createGraphics();
                        g2d.setColor(Color.RED);
                        g2d.fillRect(0,0,100,100);
                        g2d.setColor(Color.BLACK);
                        g2d.drawString("Test", 10, 50);
                        g2d.dispose();
                        ImageIO.write(dummyImage, "png", screenshotFile);
                        System.out.println("Wrote dummy screenshot to: " + screenshotFile.getAbsolutePath());
                        return screenshotFile.getAbsolutePath();
                    } catch (IOException e) {
                        System.err.println("IOException while writing dummy screenshot: " + e.getMessage());
                        return null;
                    }
                }
                return null;
            }

            Robot robot = new Robot();
            Rectangle screenRect = new Rectangle(Toolkit.getDefaultToolkit().getScreenSize());
            // For multi-monitor, one would iterate GraphicsDevice[] and capture each.
            // GraphicsEnvironment ge = GraphicsEnvironment.getLocalGraphicsEnvironment();
            // GraphicsDevice[] screens = ge.getScreenDevices();
            // For now, capture primary screen.
            BufferedImage screenCapture = robot.createScreenCapture(screenRect);
            ImageIO.write(screenCapture, "png", screenshotFile);
            System.out.println("Screenshot saved to: " + screenshotFile.getAbsolutePath());
            return screenshotFile.getAbsolutePath();

        } catch (AWTException e) {
            System.err.println("AWTException while taking screenshot: " + e.getMessage());
            e.printStackTrace();
        } catch (IOException e) {
            System.err.println("IOException while saving screenshot: " + e.getMessage());
            e.printStackTrace();
        }
        return null;
    }

    public String getDataFolder() {
        return dataFolder;
    }

    // Main method for basic testing
    public static void main(String[] args) {
        // Create a dummy ConfigManager for testing ScreenshotTaker directly
        ConfigManager mockConfig = new ConfigManager("test-screenshot-config") {
            @Override
            public String getString(String key, String defaultValue) {
                if ("dataFolder".equals(key)) {
                    return "test_screenshots_output";
                }
                return super.getString(key, defaultValue);
            }
        };
        // Ensure the test output directory for config is cleaned up or managed
        new File("test-screenshot-config").mkdirs();


        ScreenshotTaker taker = new ScreenshotTaker(mockConfig);
        String path = taker.takeScreenshot();
        if (path != null) {
            System.out.println("Screenshot taken successfully: " + path);
        } else {
            System.out.println("Failed to take screenshot.");
        }
        
        // Clean up dummy config file and directory
        File dummyCfg = new File("test-screenshot-config/config.properties");
        if(dummyCfg.exists()) dummyCfg.delete();
        new File("test-screenshot-config").delete();

        // Clean up screenshot directory if needed (or keep for inspection)
        // new File(taker.getDataFolder()).delete(); // Careful with this
    }
}
