package com.gymarena.challenge;

import java.util.Optional;

/** Persistence port; realized by SqlChallengeStore (gymarena_challenge). */
public interface IChallengeStore {
    Optional<ChallengeRuleVersion> findRuleVersion(String ruleId);

    Optional<ChallengeRuleVersion> findApprovedRule(String exercise, int level);

    /** Approved level from current_levels (FR-13.2). */
    Optional<Integer> findCurrentLevel(String memberId, String exercise);

    /** Saves the approved version and the superseded one (may be null) in one transaction. */
    void saveApproval(ChallengeRuleVersion approved, ChallengeRuleVersion superseded);

    void saveRejection(ChallengeRuleVersion rejected);
}
