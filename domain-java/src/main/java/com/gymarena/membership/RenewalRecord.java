package com.gymarena.membership;

import java.time.Instant;
import java.time.LocalDate;
import java.util.Objects;

/** Retained renewal history entry (FR-04.2). */
public record RenewalRecord(
        String memberId,
        LocalDate previousExpiry,
        LocalDate revisedExpiry,
        String recordedBy,
        Instant recordedAt) {

    public RenewalRecord {
        Objects.requireNonNull(memberId, "memberId");
        Objects.requireNonNull(previousExpiry, "previousExpiry");
        Objects.requireNonNull(revisedExpiry, "revisedExpiry");
        Objects.requireNonNull(recordedBy, "recordedBy");
        Objects.requireNonNull(recordedAt, "recordedAt");
    }
}
