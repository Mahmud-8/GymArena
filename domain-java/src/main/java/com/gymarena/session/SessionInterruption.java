package com.gymarena.session;

import java.time.Instant;

/** One pause or stop recorded against the session (FR-06.6). */
public record SessionInterruption(InterruptionReason reason, String position, Instant at) {
}
