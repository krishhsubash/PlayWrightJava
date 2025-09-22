package com.example.tests;

import com.microsoft.playwright.*;
import com.example.tests.extensions.ScreenshotOnFailureExtension;
import com.example.tests.extensions.RetryExtension;
import com.example.tests.util.AttemptContext;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

@ExtendWith({ScreenshotOnFailureExtension.class, RetryExtension.class})
public class BaseTest {
    protected static Playwright playwright;
    protected static Browser browser;
    protected BrowserContext context;
    protected Page page;
    private BufferedWriter consoleWriter;
    private Path consoleLogPath;

    @BeforeAll
    static void globalSetup() {
        if (playwright == null) {
            playwright = Playwright.create();
        }
        String browserName = System.getProperty("browser", "chromium").toLowerCase();
        boolean headed = Boolean.parseBoolean(System.getProperty("headed", "false"));

        BrowserType.LaunchOptions options = new BrowserType.LaunchOptions().setHeadless(!headed);
        switch (browserName) {
            case "firefox" -> browser = playwright.firefox().launch(options);
            case "webkit" -> browser = playwright.webkit().launch(options);
            case "chrome" -> browser = playwright.chromium().launch(options.setChannel("chrome"));
            default -> browser = playwright.chromium().launch(options);
        }
    }
    @BeforeEach
    void createContext(TestInfo testInfo) {
        Browser.NewContextOptions options = new Browser.NewContextOptions();
        boolean recordVideo = Boolean.parseBoolean(System.getProperty("recordVideo", "false"));
        if (recordVideo) {
            options.setRecordVideoDir(Paths.get("playwright-report/videos"));
        }
        context = browser.newContext(options);
        page = context.newPage();
        // Prepare console log capture
        String prefix = testInfo.getTestClass().map(Class::getSimpleName).orElse("Test") + "_" + sanitize(testInfo.getTestMethod().map(m -> m.getName()).orElse("method"));
        String attempt = String.valueOf(AttemptContext.getAttempt());
        String timestamp = DateTimeFormatter.ofPattern("yyyyMMddHHmmss").format(LocalDateTime.now());
        String baseName = prefix + "-attempt" + attempt + "-" + timestamp;
        try {
            Path logsDir = Paths.get("playwright-report/logs");
            Files.createDirectories(logsDir);
            consoleLogPath = logsDir.resolve(baseName + ".log");
            consoleWriter = Files.newBufferedWriter(consoleLogPath);
        } catch (IOException e) {
            consoleWriter = null; // fail silently
        }
        if (page != null) {
            page.onConsoleMessage(msg -> {
                if (consoleWriter != null) {
                    try {
                        consoleWriter.write("[" + msg.type() + "] " + msg.text().replaceAll("\n", " ") + System.lineSeparator());
                    } catch (IOException ignored) {}
                }
            });
        }
        boolean traceEnabled = Boolean.parseBoolean(System.getProperty("trace", "false"));
        if (testInfo.getTags().contains("no-artifacts")) {
            traceEnabled = false;
        }
        if (traceEnabled) {
            context.tracing().start(new Tracing.StartOptions().setScreenshots(true).setSnapshots(true));
        }
    }

    @AfterEach
    void teardownContext(TestInfo testInfo) {
        boolean traceEnabled = Boolean.parseBoolean(System.getProperty("trace", "false"));
        if (testInfo.getTags().contains("no-artifacts")) {
            traceEnabled = false;
        }
        if (traceEnabled) {
            String prefix = testInfo.getTestClass().map(Class::getSimpleName).orElse("Test") + "_" + sanitize(testInfo.getTestMethod().map(m -> m.getName()).orElse("method"));
            String attempt = String.valueOf(AttemptContext.getAttempt());
            String timestamp = DateTimeFormatter.ofPattern("yyyyMMddHHmmss").format(LocalDateTime.now());
            String traceName = prefix + "-attempt" + attempt + "-" + timestamp;
            context.tracing().stop(new Tracing.StopOptions().setPath(Paths.get("playwright-report/traces/" + traceName + ".zip")));
            boolean recordVideo = Boolean.parseBoolean(System.getProperty("recordVideo", "false"));
            if (recordVideo && page != null && page.video() != null) {
                try {
                    page.video().saveAs(Paths.get("playwright-report/videos/" + traceName + ".webm"));
                } catch (Exception ignored) {}
            }
        }
        if (consoleWriter != null) {
            try { consoleWriter.flush(); consoleWriter.close(); } catch (IOException ignored) {}
        }
        if (context != null) context.close();
    }

    private String sanitize(String name) {
        return name.replaceAll("[^a-zA-Z0-9-_]", "_");
    }

    @AfterAll
    static void globalTeardown() {
        if (browser != null) browser.close();
        if (playwright != null) playwright.close();
    }
}
