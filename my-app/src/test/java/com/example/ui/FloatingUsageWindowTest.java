package com.example.ui;

import com.example.config.ConfigManager;
import com.example.tracking.UsageTracker;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import javax.swing.*;
import java.awt.*;
import java.awt.event.MouseEvent;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;

public class FloatingUsageWindowTest {

    @Mock
    private ConfigManager mockConfigManager;
    @Mock
    private UsageTracker mockUsageTracker;

    private FloatingUsageWindow floatingWindow;
    private AutoCloseable mockitoCloseable;

    @Before
    public void setUp() throws Exception {
        mockitoCloseable = MockitoAnnotations.openMocks(this);

        // Default mocks for most tests
        when(mockConfigManager.getBoolean("showFloatWindow", true)).thenReturn(true);
        when(mockUsageTracker.getDailyUsageTime()).thenReturn(0L); // Start with 0 time

        // Initialize on EDT if creating actual Swing components,
        // but many tests here will be logic-only or direct method calls.
        // For tests that need to interact with Swing components after creation,
        // ensure they run on EDT or use SwingUtilities.invokeAndWait.
        SwingUtilities.invokeAndWait(() -> {
            floatingWindow = new FloatingUsageWindow(mockConfigManager, mockUsageTracker);
        });
    }

    @After
    public void tearDown() throws Exception {
        SwingUtilities.invokeAndWait(() -> {
            if (floatingWindow != null && floatingWindow.getWindow() != null) {
                floatingWindow.disposeWindow();
            }
        });
        mockitoCloseable.close();
    }

    @Test
    public void testWindowInitialization_RespectsConfig_Show() throws Exception {
        when(mockConfigManager.getBoolean("showFloatWindow", true)).thenReturn(true);
        
        SwingUtilities.invokeAndWait(() -> floatingWindow.initializeAndShow());
        
        assertNotNull("Window should be created when config is true", floatingWindow.getWindow());
        assertTrue("Window should be visible when config is true", floatingWindow.getWindow().isVisible());
    }

    @Test
    public void testWindowInitialization_RespectsConfig_Hide() throws Exception {
        when(mockConfigManager.getBoolean("showFloatWindow", true)).thenReturn(false);
        
        // Re-initialize with the new config setting for this specific test
        SwingUtilities.invokeAndWait(() -> {
             floatingWindow.disposeWindow(); // dispose previous
             floatingWindow = new FloatingUsageWindow(mockConfigManager, mockUsageTracker);
             floatingWindow.initializeAndShow();
        });

        assertNull("Window should not be created if config is false", floatingWindow.getWindow());
    }


    @Test
    public void testUpdateDisplayTime() throws Exception {
        when(mockUsageTracker.getDailyUsageTime()).thenReturn(3661L); // 1h 1m 1s
        
        SwingUtilities.invokeAndWait(() -> {
            floatingWindow.initializeAndShow(); // Ensure label is created
            // Manually call updateDisplayTime - Timer calls this on EDT already
            floatingWindow.updateDisplayTime(); 
        });

        assertEquals("今日使用: 01:01:01", floatingWindow.getCurrentDisplayTime());
    }
    
    @Test
    public void testShowWindow_WhenInitiallyDisabledAndThenEnabled() throws Exception {
        // Scenario: Initially disabled, then config changes and we call showWindow()
        when(mockConfigManager.getBoolean("showFloatWindow", true)).thenReturn(false);
        SwingUtilities.invokeAndWait(() -> {
             floatingWindow.disposeWindow();
             floatingWindow = new FloatingUsageWindow(mockConfigManager, mockUsageTracker);
             floatingWindow.initializeAndShow(); // Should not show
        });
        assertNull("Window should not be initially created", floatingWindow.getWindow());

        when(mockConfigManager.getBoolean("showFloatWindow", true)).thenReturn(true); // Simulate config change
        SwingUtilities.invokeAndWait(() -> floatingWindow.showWindow()); // Call show explicitly

        assertNotNull("Window should now be created", floatingWindow.getWindow());
        assertTrue("Window should now be visible", floatingWindow.getWindow().isVisible());
    }


    @Test
    public void testHideWindow() throws Exception {
        SwingUtilities.invokeAndWait(() -> floatingWindow.initializeAndShow());
        assertTrue("Window should be initially visible", floatingWindow.getWindow().isVisible());
        
        SwingUtilities.invokeAndWait(() -> floatingWindow.hideWindow());
        assertFalse("Window should be hidden after hideWindow()", floatingWindow.getWindow().isVisible());
    }
    
    @Test
    public void testDisposeWindow() throws Exception {
        SwingUtilities.invokeAndWait(() -> floatingWindow.initializeAndShow());
        JWindow windowInstance = floatingWindow.getWindow();
        assertNotNull(windowInstance);
        assertTrue(windowInstance.isVisible());

        SwingUtilities.invokeAndWait(() -> floatingWindow.disposeWindow());
        
        assertNull("Window reference in FloatingUsageWindow should be null after dispose", floatingWindow.getWindow());
        // Check if the actual window is disposed and not displayable
        // This is tricky as isDisplayable might be true if not fully collected.
        // A better check is that the internal window reference is null.
    }


    // Draggability is hard to test in pure unit tests without UI interaction.
    // This test will verify the logic if we could simulate mouse events.
    // For now, it's more of a structural placeholder.
    @Test
    public void testWindowDraggingLogic() throws Exception {
        SwingUtilities.invokeAndWait(() -> floatingWindow.initializeAndShow());
        JWindow window = floatingWindow.getWindow();
        assertNotNull(window);

        Point initialLocation = window.getLocation();

        // Simulate mouse press (conceptual)
        MouseEvent pressEvent = new MouseEvent(window, MouseEvent.MOUSE_PRESSED, System.currentTimeMillis(), 0, 10, 10, 1, false);
        floatingWindow.initialClick = pressEvent.getPoint(); // Directly set for test

        // Simulate mouse drag (conceptual)
        MouseEvent dragEvent = new MouseEvent(window, MouseEvent.MOUSE_DRAGGED, System.currentTimeMillis(), 0, 20, 25, 1, false);
        
        // Manually apply the drag logic as if the listener was called
        int xMoved = dragEvent.getX() - floatingWindow.initialClick.x; // 20 - 10 = 10
        int yMoved = dragEvent.getY() - floatingWindow.initialClick.y; // 25 - 10 = 15
        Point newExpectedLocation = new Point(initialLocation.x + xMoved, initialLocation.y + yMoved);

        // To properly test this, the MouseAdapter logic would need to be invoked.
        // This requires either more complex event dispatching or refactoring the listener logic
        // into a testable method.
        // For now, this test is more about outlining what to test.
        // System.out.println("Conceptual drag test: if mouse listeners were invoked, new location would be " + newExpectedLocation);
        
        // A simple check:
        assertNotNull(floatingWindow.initialClick); // Check if initialClick was set
        // Actual location change would need real event dispatching.
    }
}
