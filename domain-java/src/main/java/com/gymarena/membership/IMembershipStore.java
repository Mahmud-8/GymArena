package com.gymarena.membership;

import java.util.Optional;

/** Persistence port; realized by SqlMembershipStore (gymarena_membership). */
public interface IMembershipStore {
    Optional<Membership> findByMemberId(String memberId);

    /** Saves the revised membership and its renewal record in one transaction. */
    void saveRenewal(Membership membership, RenewalRecord record);
}
