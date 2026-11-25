package com.gymarena.session;

import java.time.Duration;
import java.util.Objects;

/** Fixed rule record copied from IChallenge when the session is created (FR-05.2). */
public record RuleSnapshot(String exercise, int level, int targetRepetitions,
                           Duration timeLimit, int ruleVersion, boolean ranked) {

    public RuleSnapshot {
        Objects.requireNonNull(exercise, "exercise");
        Objects.requireNonNull(timeLimit, "timeLimit");
        if (targetRepetitions <= 0) {
            throw new IllegalArgumentException("targetRepetitions must be positive");
        }
        if (timeLimit.isNegative() || timeLimit.isZero()) {
            throw new IllegalArgumentException("timeLimit must be positive");
        }
    }
}
