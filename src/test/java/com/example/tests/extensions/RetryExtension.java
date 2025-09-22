package com.example.tests.extensions;

import com.example.tests.util.AttemptContext;
import org.junit.jupiter.api.extension.*;

import java.lang.reflect.Method;
import java.nio.file.*;
import java.time.Instant;

class RetryLogEntry {
    static void write(String className, String methodName, int attempt, boolean success, Throwable error, int max) {
        try {
            Path targetDir = Paths.get("target");
            Files.createDirectories(targetDir);
            Path log = targetDir.resolve("retry-attempts.jsonl");
            String json = String.format("{\"timestamp\":\"%s\",\"class\":\"%s\",\"method\":\"%s\",\"attempt\":%d,\"maxRetries\":%d,\"success\":%s,\"errorType\":%s}\n",
                    Instant.now().toString(), className, methodName, attempt, max,
                    success ? "true" : "false",
                    error == null ? "null" : ('"' + error.getClass().getSimpleName() + '"'));
            Files.writeString(log, json, StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (Exception ignored) {}
    }
}

public class RetryExtension implements InvocationInterceptor {
    private static int maxRetries() {
        String prop = System.getProperty("retry.max", "0");
        try { return Integer.parseInt(prop); } catch (NumberFormatException e) { return 0; }
    }

    @Override
    public void interceptTestMethod(Invocation<Void> invocation, ReflectiveInvocationContext<Method> invocationContext, ExtensionContext extensionContext) throws Throwable {
        int max = maxRetries();
        int attempt = 1;
        Throwable last = null;
        while (attempt <= Math.max(1, max + 1)) { // first attempt + retries
            AttemptContext.setAttempt(attempt);
            try {
                invocation.proceed();
                RetryLogEntry.write(extensionContext.getRequiredTestClass().getName(), extensionContext.getRequiredTestMethod().getName(), attempt, true, null, max);
                return;
            } catch (Throwable t) {
                last = t;
                RetryLogEntry.write(extensionContext.getRequiredTestClass().getName(), extensionContext.getRequiredTestMethod().getName(), attempt, false, t, max);
                if (attempt > max) {
                    throw last;
                }
            } finally {
                AttemptContext.clear();
            }
            attempt++;
        }
        if (last != null) throw last;
    }
}
