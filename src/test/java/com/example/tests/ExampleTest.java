package com.example.tests;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

public class ExampleTest extends BaseTest {

    @Test
    @DisplayName("Should load Playwright homepage and verify title")
    void testPlaywrightHomePage() {
        page.navigate("https://playwright.dev/");
        String title = page.title();
        assertThat(title).containsIgnoringCase("Playwright");
    }
}
