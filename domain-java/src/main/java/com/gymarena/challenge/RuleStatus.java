package com.gymarena.challenge;

/** States of a {@link ChallengeRuleVersion} (FR-14.1). */
public enum RuleStatus {
    DRAFT,
    APPROVED,
    REJECTED,
    SUPERSEDED;

    public boolean isFinal() {
        return this == REJECTED || this == SUPERSEDED;
    }
}
