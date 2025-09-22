package com.example.tests.util;

public final class AttemptContext {
    private static final ThreadLocal<Integer> CURRENT = ThreadLocal.withInitial(() -> 1);
    private AttemptContext() {}
    public static int getAttempt() { return CURRENT.get(); }
    public static void setAttempt(int attempt) { CURRENT.set(Math.max(1, attempt)); }
    public static void clear() { CURRENT.remove(); }
}
