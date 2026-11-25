package com.gymarena.membership;

import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.util.Objects;

/** Control class for "Record a membership renewal" (US-07 / GYM-21, FR-04). */
public class RenewalProcessor {

    private final IMemberLookup memberLookup;
    private final IMembershipStore store;
    private final IRenewalFeed renewalFeed;
    private final Clock clock;

    public RenewalProcessor(IMemberLookup memberLookup, IMembershipStore store,
                            IRenewalFeed renewalFeed, Clock clock) {
        this.memberLookup = Objects.requireNonNull(memberLookup);
        this.store = Objects.requireNonNull(store);
        this.renewalFeed = Objects.requireNonNull(renewalFeed);
        this.clock = Objects.requireNonNull(clock);
    }

    /** Message 1 of the collaboration diagram. */
    public RenewalRecord renew(String memberId, LocalDate revisedExpiry, String staffId) {
        if (!memberLookup.exists(memberId)) {                                  // 1.1
            throw new MemberNotFoundException(memberId);
        }
        Membership membership = store.findByMemberId(memberId)                 // 1.2
                .orElseThrow(() -> new IllegalStateException("No membership for " + memberId));
        Instant now = clock.instant();
        LocalDate today = LocalDate.ofInstant(now, clock.getZone());
        RenewalRecord record = membership.renew(revisedExpiry, staffId, now, today); // 1.3
        store.saveRenewal(membership, record);                                 // 1.4
        renewalFeed.publish(RenewalChanged.from(record));                      // 1.5
        return record;
    }
}
