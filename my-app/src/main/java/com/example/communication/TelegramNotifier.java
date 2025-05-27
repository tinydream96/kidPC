package com.example.communication;

import com.example.config.ConfigManager;
import com.example.screenshot.ScreenshotTaker;
import com.example.tracking.UsageTracker;
import okhttp3.*;

import java.io.File;
import java.io.IOException;
import java.net.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.TimeUnit;

public class TelegramNotifier {

    private final ConfigManager configManager;
    private final UsageTracker usageTracker;
    private final ScreenshotTaker screenshotTaker;
    private OkHttpClient httpClient;

    private static final int MAX_RETRIES = 3;
    private static final long RETRY_DELAY_MS = 1000; // 1 second

    public TelegramNotifier(ConfigManager configManager, UsageTracker usageTracker, ScreenshotTaker screenshotTaker) {
        this.configManager = configManager;
        this.usageTracker = usageTracker;
        this.screenshotTaker = screenshotTaker;
        this.httpClient = buildHttpClient();
    }

    private OkHttpClient buildHttpClient() {
        OkHttpClient.Builder builder = new OkHttpClient.Builder()
                .connectTimeout(15, TimeUnit.SECONDS)
                .writeTimeout(15, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS);

        String proxySetting = configManager.getString("proxy", "");
        if (proxySetting != null && !proxySetting.isEmpty()) {
            try {
                URL proxyUrl = new URL(proxySetting);
                Proxy.Type type = proxyUrl.getProtocol().equalsIgnoreCase("socks5") ? Proxy.Type.SOCKS : Proxy.Type.HTTP;
                InetSocketAddress proxyAddress = new InetSocketAddress(proxyUrl.getHost(), proxyUrl.getPort());
                builder.proxy(new Proxy(type, proxyAddress));

                String userInfo = proxyUrl.getUserInfo();
                if (userInfo != null) {
                    String[] credentials = userInfo.split(":", 2);
                    if (credentials.length == 2) {
                        String username = credentials[0];
                        String password = credentials[1];
                        builder.proxyAuthenticator((route, response) -> {
                            String credential = Credentials.basic(username, password);
                            return response.request().newBuilder()
                                    .header("Proxy-Authorization", credential)
                                    .build();
                        });
                    }
                }
                System.out.println("Using proxy: " + proxyUrl.getHost() + ":" + proxyUrl.getPort());
            } catch (MalformedURLException e) {
                System.err.println("Invalid proxy URL format: " + proxySetting + ". Error: " + e.getMessage());
            } catch (IllegalArgumentException e) {
                System.err.println("Invalid proxy address or port for: " + proxySetting + ". Error: " + e.getMessage());
            }
        }
        return builder.build();
    }

    private String getLocalIpAddress() {
        try (final DatagramSocket socket = new DatagramSocket()) {
            socket.connect(InetAddress.getByName("8.8.8.8"), 10002); // Google's public DNS on an arbitrary port
            return socket.getLocalAddress().getHostAddress();
        } catch (SocketException | UnknownHostException e) {
            System.err.println("Could not determine local IP address: " + e.getMessage());
            try {
                return InetAddress.getLocalHost().getHostAddress();
            } catch (UnknownHostException ex) {
                System.err.println("Could not determine local IP via getLocalHost(): " + ex.getMessage());
                return "IP N/A";
            }
        }
    }

    public boolean sendScreenshotWithDetails() {
        String botToken = configManager.getString("botToken", null);
        String chatId = configManager.getString("chatId", null);

        if (botToken == null || botToken.isEmpty() || botToken.equals("YOUR_BOT_TOKEN")) {
            System.err.println("Telegram Bot Token is not configured. Aborting send.");
            return false;
        }
        if (chatId == null || chatId.isEmpty() || chatId.equals("YOUR_CHAT_ID")) {
            System.err.println("Telegram Chat ID is not configured. Aborting send.");
            return false;
        }

        String screenshotPath = screenshotTaker.takeScreenshot();
        if (screenshotPath == null) {
            System.err.println("Failed to take screenshot. Aborting send.");
            return false;
        }
        File screenshotFile = new File(screenshotPath);

        try {
            String ipAddress = getLocalIpAddress();
            String currentTime = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
            String formattedUsageTime = UsageTracker.formatTime(usageTracker.getDailyUsageTime());
            String formattedContinuousUsageTime = UsageTracker.formatTime(usageTracker.getContinuousUsageTime());

            String caption = String.format("IP: %s\nTime: %s\nDaily Usage: %s\nContinuous Usage: %s",
                    ipAddress, currentTime, formattedUsageTime, formattedContinuousUsageTime);

            String url = "https://api.telegram.org/bot" + botToken + "/sendPhoto";

            RequestBody requestBody = new MultipartBody.Builder()
                    .setType(MultipartBody.FORM)
                    .addFormDataPart("chat_id", chatId)
                    .addFormDataPart("photo", screenshotFile.getName(),
                            RequestBody.create(screenshotFile, MediaType.parse("image/png")))
                    .addFormDataPart("caption", caption)
                    .build();

            Request request = new Request.Builder()
                    .url(url)
                    .post(requestBody)
                    .build();

            boolean success = false;
            for (int i = 0; i < MAX_RETRIES; i++) {
                try {
                    System.out.println("Attempt " + (i + 1) + " to send screenshot to Telegram...");
                    Response response = httpClient.newCall(request).execute();
                    if (response.isSuccessful()) {
                        System.out.println("Screenshot sent successfully to Telegram.");
                        ResponseBody responseBody = response.body();
                        if(responseBody != null) {
                            System.out.println("Telegram API Response: " + responseBody.string());
                            responseBody.close();
                        }
                        success = true;
                        break; 
                    } else {
                        System.err.println("Failed to send screenshot. Telegram API Response Code: " + response.code());
                        ResponseBody responseBody = response.body();
                         if(responseBody != null) {
                            System.err.println("Telegram API Error: " + responseBody.string());
                            responseBody.close();
                        }
                    }
                    response.close(); // Ensure response is closed
                } catch (IOException e) {
                    System.err.println("IOException during attempt " + (i + 1) + " to send screenshot: " + e.getMessage());
                    if (i < MAX_RETRIES - 1) {
                        Thread.sleep(RETRY_DELAY_MS * (i + 1)); // Exponential backoff could be better
                    } else {
                         System.err.println("Max retries reached. Giving up on sending screenshot.");
                    }
                }
            }
            return success;

        } catch (InterruptedException e) {
            System.err.println("Screenshot sending was interrupted: " + e.getMessage());
            Thread.currentThread().interrupt();
            return false;
        } finally {
            if (screenshotFile.exists()) {
                if (!screenshotFile.delete()) {
                    System.err.println("Failed to delete local screenshot file: " + screenshotPath);
                } else {
                    System.out.println("Local screenshot file deleted: " + screenshotPath);
                }
            }
        }
    }
    
    // Main for quick manual test
    public static void main(String[] args) {
        // Create dummy instances for testing.
        // In a real app, these would be properly initialized.
        ConfigManager cm = new ConfigManager("telegram-notifier-test-config");
        // Ensure config file has botToken and chatId for testing
        // cm.setSetting("botToken", "YOUR_ACTUAL_BOT_TOKEN_FOR_TESTING");
        // cm.setSetting("chatId", "YOUR_ACTUAL_CHAT_ID_FOR_TESTING");
        // cm.setSetting("proxy", "http://yourproxy:port"); // Optional: if you need to test proxy
        // cm.saveConfig();


        UsageTracker ut = new UsageTracker(cm); // Dummy, usage will be 0
        ScreenshotTaker st = new ScreenshotTaker(cm);

        TelegramNotifier notifier = new TelegramNotifier(cm, ut, st);
        boolean sent = notifier.sendScreenshotWithDetails();
        System.out.println("Notification sent: " + sent);

        // Clean up dummy config
        new File("telegram-notifier-test-config/config.properties").delete();
        new File("telegram-notifier-test-config").delete();
    }
}
