package com.gymarena.member;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;

/** Test fixtures = the objects of the Member Management object diagram (PM2 Figure A1-W). */
final class MeasurementFixtures {

    static final String MEMBER_ID = "MBR-0042";
    static final String READING_ID = "WR-0310";
    static final Instant READ_AT = Instant.parse("2026-11-22T09:40:12Z");
    static final Instant CONFIRMED_AT = Instant.parse("2026-11-22T09:40:30Z");
    static final Clock CLOCK = Clock.fixed(CONFIRMED_AT, ZoneOffset.UTC);

    private MeasurementFixtures() {
    }

    /** omar : MemberProfile {memberId="MBR-0042", name="Omar Adel", age=24, memberCode="GA-7Q4K"}. */
    static MemberProfile omar() {
        return new MemberProfile(MEMBER_ID, "Omar Adel", 24, "GA-7Q4K");
    }

    /** raw : ScaleReading {weightKg=78.4, stable=true, readAt=09:40:12}. */
    static ScaleReading stableReading() {
        return new ScaleReading(78.4, true, READ_AT);
    }

    /** wr310 : WeightReading {readingId="WR-0310", weightKg=78.4, status=PENDING_CONFIRMATION}. */
    static WeightReading pendingReading() {
        return WeightReading.capture(READING_ID, omar(), stableReading());
    }
}
