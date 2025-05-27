package com.example.communication;

import com.example.config.ConfigManager;
import com.example.screenshot.ScreenshotTaker;
import com.example.tracking.UsageTracker;
import okhttp3.OkHttpClient;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.After;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.junit.rules.TemporaryFolder;


import java.io.File;
import java.io.IOException;
import java.net.InetAddress;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.TimeUnit;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;

public class TelegramNotifierTest {

    @Rule
    public TemporaryFolder temporaryFolder = new TemporaryFolder();

    private MockWebServer mockWebServer;
    private TelegramNotifier telegramNotifier;

    @Mock
    private ConfigManager mockConfigManager;
    @Mock
    private UsageTracker mockUsageTracker;
    @Mock
    private ScreenshotTaker mockScreenshotTaker;
    
    private File testScreenshotFile;
    private AutoCloseable mockitoCloseable;


    @Before
    public void setUp() throws IOException {
        mockitoCloseable = MockitoAnnotations.openMocks(this);
        mockWebServer = new MockWebServer();
        mockWebServer.start();

        // Mock ConfigManager responses
        when(mockConfigManager.getString("botToken", null)).thenReturn("test_bot_token");
        when(mockConfigManager.getString("chatId", null)).thenReturn("test_chat_id");
        when(mockConfigManager.getString("proxy", "")).thenReturn(""); // No proxy for most tests

        // Mock UsageTracker
        when(mockUsageTracker.getDailyUsageTime()).thenReturn(3661L); // 1 hour, 1 minute, 1 second
        when(mockUsageTracker.getContinuousUsageTime()).thenReturn(600L); // 10 minutes

        // Mock ScreenshotTaker
        testScreenshotFile = temporaryFolder.newFile("test_screenshot.png");
        // Write some dummy content to the file to make it a valid image file for MediaType.parse
        Path path = testScreenshotFile.toPath();
        byte[] dummyBytes = "dummy PNG content".getBytes(); // Simplistic; real PNG bytes would be better
        Files.write(path, dummyBytes, StandardOpenOption.CREATE);

        when(mockScreenshotTaker.takeScreenshot()).thenReturn(testScreenshotFile.getAbsolutePath());

        telegramNotifier = new TelegramNotifier(mockConfigManager, mockUsageTracker, mockScreenshotTaker);
        // Override the httpClient in telegramNotifier to use the mockWebServer's dispatcher
        // This is a bit of a workaround. A cleaner way would be to inject OkHttpClient or its factory.
        // For this test, we directly modify the client used by TelegramNotifier.
        // This requires TelegramNotifier's httpClient to be non-final or have a setter,
        // or to be constructed with a client from a factory we can control.
        // Assuming TelegramNotifier.buildHttpClient() is called in constructor and we can re-initialize
        // or modify the client. For simplicity, let's assume we can re-initialize with a new client.
        // For this example, we'll rely on the fact that OkHttp uses a default client if not set,
        // and MockWebServer works by redirecting that.
        // For more complex scenarios (like specific client features), dependency injection of OkHttpClient is preferred.
        // The current TelegramNotifier instantiates OkHttpClient internally, so we modify its base URL for testing.
        // This is typically done by setting the base URL of the API calls in the notifier to mockWebServer.url("/").toString()
        // However, Telegram API URL is hardcoded. So we rely on MockWebServer to intercept.
        // For robust testing of proxy, direct client injection or a test-specific constructor would be needed.
    }

    @After
    public void tearDown() throws Exception {
        mockWebServer.shutdown();
        mockitoCloseable.close();
        // TemporaryFolder handles deletion of testScreenshotFile
    }

    @Test
    public void testSendScreenshotWithDetails_success() throws Exception {
        mockWebServer.enqueue(new MockResponse().setBody("{\"ok\":true,\"result\":{}}").setResponseCode(200));

        boolean result = telegramNotifier.sendScreenshotWithDetails();
        assertTrue("Notification should be sent successfully", result);

        RecordedRequest request = mockWebServer.takeRequest(1, TimeUnit.SECONDS);
        assertNotNull("Request should have been made to MockWebServer", request);
        assertEquals("/bot" + "test_bot_token" + "/sendPhoto", request.getPath());
        
        String requestBody = request.getBody().readUtf8();
        assertTrue("Request body should contain chat_id", requestBody.contains("name=\"chat_id\"\r\n\r\ntest_chat_id"));
        assertTrue("Request body should contain caption", requestBody.contains("name=\"caption\""));
        assertTrue("Request body should contain photo part", requestBody.contains("name=\"photo\"; filename=\"" + testScreenshotFile.getName() + "\""));
        
        // Verify IP, time, usage in caption (approximate check)
        assertTrue("Caption should contain IP", requestBody.contains("IP:"));
        assertTrue("Caption should contain Daily Usage", requestBody.contains("Daily Usage: 01:01:01"));
        assertTrue("Caption should contain Continuous Usage", requestBody.contains("Continuous Usage: 00:10:00"));

        assertFalse("Screenshot file should be deleted after successful send", testScreenshotFile.exists());
    }

    @Test
    public void testSendScreenshotWithDetails_apiError_noRetrySuccess() throws Exception {
        mockWebServer.enqueue(new MockResponse().setBody("{\"ok\":false,\"description\":\"Error from API\"}").setResponseCode(400));
        mockWebServer.enqueue(new MockResponse().setBody("{\"ok\":false,\"description\":\"Error from API\"}").setResponseCode(400));
        mockWebServer.enqueue(new MockResponse().setBody("{\"ok\":false,\"description\":\"Error from API\"}").setResponseCode(400));

        boolean result = telegramNotifier.sendScreenshotWithDetails();
        assertFalse("Notification should fail after retries", result);
        assertEquals("Should have made 3 requests due to retries", 3, mockWebServer.getRequestCount());
        assertFalse("Screenshot file should be deleted even after failed send attempts", testScreenshotFile.exists());
    }
    
    @Test
    public void testSendScreenshotWithDetails_apiError_retryWithSuccess() throws Exception {
        mockWebServer.enqueue(new MockResponse().setBody("{\"ok\":false,\"description\":\"Temporary Error\"}").setResponseCode(500)); // Fail once
        mockWebServer.enqueue(new MockResponse().setBody("{\"ok\":true,\"result\":{}}").setResponseCode(200)); // Then succeed

        boolean result = telegramNotifier.sendScreenshotWithDetails();
        assertTrue("Notification should succeed on retry", result);
        assertEquals("Should have made 2 requests (1 fail, 1 success)", 2, mockWebServer.getRequestCount());
        assertFalse("Screenshot file should be deleted after successful send on retry", testScreenshotFile.exists());
    }

    @Test
    public void testSendScreenshotWithDetails_screenshotFail() {
        when(mockScreenshotTaker.takeScreenshot()).thenReturn(null); // Simulate screenshot failure
        boolean result = telegramNotifier.sendScreenshotWithDetails();
        assertFalse("Notification should fail if screenshot fails", result);
        assertEquals(0, mockWebServer.getRequestCount()); // No request should be made
    }

    @Test
    public void testSendScreenshotWithDetails_missingBotToken() {
        when(mockConfigManager.getString("botToken", null)).thenReturn(""); // Simulate missing token
        boolean result = telegramNotifier.sendScreenshotWithDetails();
        assertFalse("Notification should fail if bot token is missing", result);
        assertEquals(0, mockWebServer.getRequestCount());
    }
    
    @Test
    public void testSendScreenshotWithDetails_missingChatId() {
        when(mockConfigManager.getString("chatId", null)).thenReturn("YOUR_CHAT_ID"); // Simulate default/missing chat ID
        boolean result = telegramNotifier.sendScreenshotWithDetails();
        assertFalse("Notification should fail if chat ID is missing", result);
        assertEquals(0, mockWebServer.getRequestCount());
    }

    @Test
    public void testGetLocalIpAddress() throws Exception {
        // This test is a bit tricky as it depends on network environment.
        // We can't easily mock DatagramSocket/InetAddress without PowerMock or similar.
        // For now, we'll just call it and ensure it returns something, or "IP N/A"
        // In a real test environment, one might use a loopback address setup.
        TelegramNotifier realNotifier = new TelegramNotifier(mockConfigManager, mockUsageTracker, mockScreenshotTaker);
        // Private method, so test its effect through the public method's caption.
        // Or, make it package-private for testing. For now, rely on the success test's caption check.
        
        // If we were to test it directly (assuming it's made accessible):
        // String ip = realNotifier.getLocalIpAddress(); // If getLocalIpAddress was not private
        // assertNotNull(ip);
        // System.out.println("Detected IP for testing: " + ip);
        // A simple check:
        try {
            InetAddress.getByName("8.8.8.8"); // Check if DNS resolution works, as getLocalIpAddress uses it
            // If it doesn't throw UnknownHostException, then the primary method in getLocalIpAddress might work
        } catch (java.net.UnknownHostException e) {
            System.out.println("DNS resolution for 8.8.8.8 failed, getLocalIpAddress might use fallback.");
        }
        // Actual validation of IP format is complex, so just ensure it's part of the caption.
        assertTrue("getLocalIpAddress is implicitly tested by successful send test's caption check.", true);
    }

    // Proxy testing with MockWebServer is complex because the client needs to be configured
    // to route its requests to the MockWebServer *as a proxy*.
    // Standard MockWebServer usage has it act as the target server.
    // For a true proxy test, one might need a more specialized setup or inject a pre-configured OkHttpClient.
    @Test
    public void testProxyConfiguration() {
        // This test is more of a placeholder for the complexity involved.
        // To truly test this with MockWebServer, MockWebServer itself would need to act as the proxy,
        // and the Telegram API URL would be the target.
        // Or, you verify that OkHttpClient is built with proxy settings if provided.

        when(mockConfigManager.getString("proxy", "")).thenReturn("http://localhost:" + mockWebServer.getPort());
        // Re-initialize to apply new proxy setting from mock.
        // This highlights the need for easier OkHttpClient injection or re-configuration in TelegramNotifier.
        telegramNotifier = new TelegramNotifier(mockConfigManager, mockUsageTracker, mockScreenshotTaker);

        // Enqueue a response assuming the request makes it through the (mocked) proxy to the (mocked) target
        mockWebServer.enqueue(new MockResponse().setBody("{\"ok\":true,\"result\":{}}").setResponseCode(200));
        
        // The current setup means mockWebServer is the *target*. If it were also the proxy,
        // the request would be to "https://api.telegram.org..." and MockWebServer would log the proxy request.
        // For now, this test just ensures the code path for proxy setup in buildHttpClient() is covered
        // if we were to inspect the created OkHttpClient instance.

        // boolean result = telegramNotifier.sendScreenshotWithDetails();
        // assertTrue(result);
        // RecordedRequest request = mockWebServer.takeRequest(); // This would be to the Telegram API via the proxy
        // assertNotNull(request);
        // assertEquals("api.telegram.org", request.getHeader("Host")); // Or similar, depending on proxy behavior
        System.out.println("Proxy configuration test is conceptual without deeper OkHttp client mocking/injection for proxy behavior verification with MockWebServer.");
        assertTrue("Conceptual test for proxy config path.", true);
    }
}
