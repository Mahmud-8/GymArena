package com.gymarena.membership;

import java.time.Instant;
import java.time.LocalDate;
import java.util.Objects;

/**
 * Subscription record of one member (FR-03, FR-04). The state diagram of this
 * class is NO_SUBSCRIPTION -> ACTIVE <-> EXPIRED; renew() keeps or returns it to ACTIVE.
 */
public class Membership {

    private final String memberId;
    private String whatsappNumber;
    private LocalDate startDate;
    private LocalDate expiryDate;
    private MembershipStatus status;

    public Membership(String memberId, String whatsappNumber) {
        this.memberId = requireText(memberId, "memberId");
        this.whatsappNumber = whatsappNumber;
        this.status = MembershipStatus.NO_SUBSCRIPTION;
    }

    /** Restores a stored membership (used by the repository and as a test fixture). */
    public static Membership restore(String memberId, String whatsappNumber,
                                     LocalDate startDate, LocalDate expiryDate, LocalDate today) {
        Membership membership = new Membership(memberId, whatsappNumber);
        membership.startDate = Objects.requireNonNull(startDate, "startDate");
        membership.expiryDate = Objects.requireNonNull(expiryDate, "expiryDate");
        membership.status = expiryDate.isBefore(today) ? MembershipStatus.EXPIRED : MembershipStatus.ACTIVE;
        return membership;
    }

    /** FR-03.1: NO_SUBSCRIPTION --recordSubscription(start, expiry) [expiry >= today]--> ACTIVE. */
    public void recordSubscription(LocalDate start, LocalDate expiry, LocalDate today) {
        if (status != MembershipStatus.NO_SUBSCRIPTION) {
            throw new IllegalStateException("Subscription already recorded; use renew()");
        }
        Objects.requireNonNull(start, "start");
        Objects.requireNonNull(expiry, "expiry");
        if (expiry.isBefore(start)) {
            throw new IllegalArgumentException("Expiry date must not be before start date");
        }
        if (expiry.isBefore(today)) {
            throw new IllegalArgumentException("A new subscription must not already be expired");
        }
        this.startDate = start;
        this.expiryDate = expiry;
        this.status = MembershipStatus.ACTIVE;
    }

    /** FR-03.2: ACTIVE --checkExpiry(today) [expiry < today]--> EXPIRED. */
    public MembershipStatus checkExpiry(LocalDate today) {
        if (status == MembershipStatus.ACTIVE && expiryDate.isBefore(today)) {
            status = MembershipStatus.EXPIRED;
        }
        return status;
    }

    /**
     * FR-04.1/FR-04.2: ACTIVE or EXPIRED --renew(revised) [revised > expiry and revised >= today]
     * / create RenewalRecord--> ACTIVE.
     */
    public RenewalRecord renew(LocalDate revisedExpiry, String staffId, Instant now, LocalDate today) {
        if (status == MembershipStatus.NO_SUBSCRIPTION) {
            throw new IllegalStateException("No subscription to renew");
        }
        Objects.requireNonNull(revisedExpiry, "revisedExpiry");
        requireText(staffId, "staffId");
        if (!revisedExpiry.isAfter(expiryDate)) {
            throw new IllegalArgumentException("Revised expiry must be after the current expiry " + expiryDate);
        }
        if (revisedExpiry.isBefore(today)) {
            throw new IllegalArgumentException("Revised expiry must not be in the past");
        }
        RenewalRecord record = new RenewalRecord(memberId, expiryDate, revisedExpiry, staffId, now);
        this.expiryDate = revisedExpiry;
        this.status = MembershipStatus.ACTIVE;
        return record;
    }

    /** FR-03.5. */
    public void changeWhatsappNumber(String number) {
        this.whatsappNumber = requireText(number, "number");
    }

    public String getMemberId() { return memberId; }
    public String getWhatsappNumber() { return whatsappNumber; }
    public LocalDate getStartDate() { return startDate; }
    public LocalDate getExpiryDate() { return expiryDate; }
    public MembershipStatus getStatus() { return status; }

    private static String requireText(String value, String name) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(name + " is required");
        }
        return value;
    }
}
