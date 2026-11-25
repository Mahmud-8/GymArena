package com.gymarena.challenge;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;

/** Test fixtures = the objects of the Challenge Management object diagram (PM2). */
final class ChallengeFixtures {

    static final Instant V3_APPROVED_AT = Instant.parse("2026-11-02T09:00:00Z");
    static final Instant NOW = Instant.parse("2026-11-22T11:00:00Z");
    static final Clock CLOCK = Clock.fixed(NOW, ZoneOffset.UTC);
    static final String TRAINER = "TRN-03";
    static final String MEMBER_ID = "MBR-0042";
    static final String V3_ID = "CR-SQUAT-2-v3";
    static final String V4_ID = "CR-SQUAT-2-v4";

    private ChallengeFixtures() {
    }

    /** v3 : ChallengeRuleVersion {SQUAT, level 2, version 3, target 20, 120 s, +10 / -3, APPROVED}. */
    static ChallengeRuleVersion approvedV3() {
        ChallengeRuleVersion v3 = new ChallengeRuleVersion(V3_ID, "SQUAT", 2, 3, 20, Duration.ofSeconds(120), 10, 3,
                WinnerRule.MOST_REPETITIONS);
        return ChallengeRuleVersion.approved(v3, "TRN-01", V3_APPROVED_AT);
    }

    /** v4 : ChallengeRuleVersion {SQUAT, level 2, version 4, target 22, 120 s, +12 / -3, DRAFT}. */
    static ChallengeRuleVersion draftV4() {
        return new ChallengeRuleVersion(V4_ID, "SQUAT", 2, 4, 22, Duration.ofSeconds(120), 12, 3,
                WinnerRule.MOST_REPETITIONS);
    }
}
