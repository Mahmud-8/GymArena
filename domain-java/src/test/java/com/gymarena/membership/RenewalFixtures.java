package com.gymarena.membership;

import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;

/** Test fixtures = the objects of the Membership object diagram (PM2 Figure A1-M). */
final class RenewalFixtures {

    static final Instant NOW = Instant.parse("2026-11-22T10:15:00Z");
    static final LocalDate TODAY = LocalDate.of(2026, 11, 22);
    static final Clock CLOCK = Clock.fixed(NOW, ZoneOffset.UTC);

    static final String MEMBER_ID = "MBR-0042";
    static final String WHATSAPP = "+201000000042";
    static final String STAFF_ID = "STF-07";
    static final LocalDate START = LocalDate.of(2026, 8, 1);
    static final LocalDate CURRENT_EXPIRY = LocalDate.of(2026, 11, 30);
    static final LocalDate REVISED_EXPIRY = LocalDate.of(2027, 2, 28);

    private RenewalFixtures() {
    }

    /** m42 : Membership {memberId="MBR-0042", expiryDate=2026-11-30, status=ACTIVE}. */
    static Membership activeMembership() {
        return Membership.restore(MEMBER_ID, WHATSAPP, START, CURRENT_EXPIRY, TODAY);
    }

    /** Same member after the expiry date passed: expiryDate=2026-10-31, status=EXPIRED. */
    static Membership expiredMembership() {
        return Membership.restore(MEMBER_ID, WHATSAPP, LocalDate.of(2026, 8, 1), LocalDate.of(2026, 10, 31), TODAY);
    }

    /** r1 : RenewalRecord expected after message 1.3. */
    static RenewalRecord expectedRecord() {
        return new RenewalRecord(MEMBER_ID, CURRENT_EXPIRY, REVISED_EXPIRY, STAFF_ID, NOW);
    }
}
