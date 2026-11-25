package com.gymarena.session;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;

/** Test fixtures = the objects of the Session Control object diagram (PM2 Figure A1-S). */
final class SessionFixtures {

    static final String SESSION_ID = "SES-1001";
    static final String OMAR = "MBR-0042";
    static final String SARA = "MBR-0057";
    static final Instant STARTED_AT = Instant.parse("2026-11-22T10:00:00Z");
    static final Instant LOST_AT = Instant.parse("2026-11-22T10:01:35Z");     // 95 s active
    static final Instant RESUMED_AT = Instant.parse("2026-11-22T10:02:05Z");  // 30 s paused

    private SessionFixtures() {
    }

    static Clock clockAt(Instant instant) {
        return Clock.fixed(instant, ZoneOffset.UTC);
    }

    /** rules : RuleSnapshot {exercise="SQUAT", level=2, target=20, timeLimit=120 s, version=3, ranked=true}. */
    static RuleSnapshot squatRules() {
        return new RuleSnapshot("SQUAT", 2, 20, Duration.ofSeconds(120), 3, true);
    }

    /** s1001 : ChallengeSession in CREATED with p1 (LEFT) and p2 (RIGHT). */
    static ChallengeSession createdSession() {
        return new ChallengeSession(SESSION_ID, SessionMode.LOCAL_1V1, squatRules(),
                List.of(new SessionParticipant(OMAR, "LEFT"), new SessionParticipant(SARA, "RIGHT")));
    }

    /** s1001 ACTIVE since 10:00:00 with p1.count=14 and p2.count=12. */
    static ChallengeSession activeSession() {
        ChallengeSession s = createdSession();
        s.start(true, STARTED_AT);
        for (int i = 0; i < 14; i++) {
            s.addRepetition(OMAR);
        }
        for (int i = 0; i < 12; i++) {
            s.addRepetition(SARA);
        }
        return s;
    }

    /** s1001 PAUSED at 10:01:35 after TRACKING_LOST at RIGHT; activeTime = 95 s. */
    static ChallengeSession pausedSession() {
        ChallengeSession s = activeSession();
        s.pause(InterruptionReason.TRACKING_LOST, "RIGHT", LOST_AT);
        return s;
    }
}
