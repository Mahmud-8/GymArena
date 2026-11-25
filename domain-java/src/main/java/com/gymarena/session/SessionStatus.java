package com.gymarena.session;

/** States of a {@link ChallengeSession} (FR-05, FR-06). */
public enum SessionStatus {
    CREATED,
    ACTIVE,
    PAUSED,
    COMPLETED,
    STOPPED,
    INCOMPLETE;

    public boolean isFinal() {
        return this == COMPLETED || this == STOPPED || this == INCOMPLETE;
    }
}
