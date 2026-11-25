package com.gymarena.membership;

import java.time.LocalDate;

/** Renewal-feed record consumed by Notifications through IMembership (FR-04.3). */
public record RenewalChanged(String memberId, LocalDate previousExpiry, LocalDate revisedExpiry) {

    public static RenewalChanged from(RenewalRecord record) {
        return new RenewalChanged(record.memberId(), record.previousExpiry(), record.revisedExpiry());
    }
}
