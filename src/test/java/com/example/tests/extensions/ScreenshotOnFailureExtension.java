package com.example.tests.extensions;

import com.microsoft.playwright.Page;
import org.junit.jupiter.api.extension.*;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Optional;

public class ScreenshotOnFailureExtension implements AfterTestExecutionCallback, BeforeTestExecutionCallback {
    private static final DateTimeFormatter TS = DateTimeFormatter.ofPattern("yyyyMMddHHmmss");
    private static final String SCREENSHOT_DIR = "playwright-report/screenshots";

    @Override
    public void beforeTestExecution(ExtensionContext context) {
        // Ensure directory exists
        try { Files.createDirectories(Paths.get(SCREENSHOT_DIR)); } catch (Exception ignored) {}
    }

    @Override
    public void afterTestExecution(ExtensionContext context) {
        boolean screenshotOnFail = Boolean.parseBoolean(System.getProperty("screenshotOnFail", "true"));
        if (!screenshotOnFail) return;

        Optional<Throwable> executionException = context.getExecutionException();
        if (executionException.isEmpty()) return; // only on failure

        Object testInstance = context.getRequiredTestInstance();
        Page page = ReflectionUtils.findPage(testInstance);
        if (page == null) return;

        String baseName = sanitize(context.getDisplayName()) + "_" + TS.format(LocalDateTime.now());
        Path target = Paths.get(SCREENSHOT_DIR, baseName + ".png");
        try {
            page.screenshot(new Page.ScreenshotOptions().setPath(target).setFullPage(true));
            attachToAllure(target);
        } catch (Exception ignored) {}
    }

    private void attachToAllure(Path file) {
        try {
            Class<?> allure = Class.forName("io.qameta.allure.Allure");
            Object lifecycle = allure.getMethod("getLifecycle").invoke(null);
            Class<?> lifecycleClass = lifecycle.getClass();
            lifecycleClass.getMethod("addAttachment", String.class, String.class, String.class, byte[].class)
                .invoke(lifecycle, file.getFileName().toString(), "image/png", "png", Files.readAllBytes(file));
        } catch (Exception ignored) {}
    }

    private String sanitize(String name) {
        return name.replaceAll("[^a-zA-Z0-9-_]", "_");
    }

    // simple reflection utility
    static class ReflectionUtils {
        static Page findPage(Object testInstance) {
            try {
                Class<?> cls = testInstance.getClass();
                while (cls != null) {
                    for (var f : cls.getDeclaredFields()) {
                        if (Page.class.isAssignableFrom(f.getType())) {
                            f.setAccessible(true);
                            Object val = f.get(testInstance);
                            if (val instanceof Page p) return p;
                        }
                    }
                    cls = cls.getSuperclass();
                }
            } catch (Exception ignored) {}
            return null;
        }
    }
}
