package com.gymarena.member;

import java.time.Instant;
import java.util.Objects;

/**
 * Scale reading shown to a member for confirmation (FR-10.2). State diagram:
 * PENDING_CONFIRMATION -> CONFIRMED | DISCARDED.
 */
public class WeightReading {

    private final String readingId;
    private final String memberId;
    private final double weightKg;
    private final Instant readAt;
    private ReadingStatus status;
    private Instant confirmedAt;

    private WeightReading(String readingId, String memberId, double weightKg, Instant readAt) {
        this.readingId = Objects.requireNonNull(readingId, "readingId");
        this.memberId = Objects.requireNonNull(memberId, "memberId");
        this.weightKg = weightKg;
        this.readAt = Objects.requireNonNull(readAt, "readAt");
        this.status = ReadingStatus.PENDING_CONFIRMATION;
    }

    /** [*] --capture [valid reading]--> PENDING_CONFIRMATION. */
    public static WeightReading capture(String readingId, MemberProfile member, ScaleReading reading) {
        if (!reading.isValid()) {
            throw new InvalidScaleReadingException(reading);
        }
        return new WeightReading(readingId, member.memberId(), reading.weightKg(), reading.readAt());
    }

    /** PENDING_CONFIRMATION --confirm(memberId) [same member] / stamp time--> CONFIRMED. */
    public void confirm(String confirmingMemberId, Instant now) {
        requirePending("confirm");
        if (!memberId.equals(confirmingMemberId)) {
            throw new IllegalArgumentException("Only the measured member can confirm this reading");
        }
        status = ReadingStatus.CONFIRMED;
        confirmedAt = now;
    }

    /** PENDING_CONFIRMATION --reject()--> DISCARDED. */
    public void reject() {
        requirePending("reject");
        status = ReadingStatus.DISCARDED;
    }

    private void requirePending(String operation) {
        if (status != ReadingStatus.PENDING_CONFIRMATION) {
            throw new IllegalStateException("Cannot " + operation + " a reading in state " + status);
        }
    }

    public String getReadingId() { return readingId; }
    public String getMemberId() { return memberId; }
    public double getWeightKg() { return weightKg; }
    public Instant getReadAt() { return readAt; }
    public ReadingStatus getStatus() { return status; }
    public Instant getConfirmedAt() { return confirmedAt; }
}
