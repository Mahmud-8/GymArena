package com.gymarena.challenge;

import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;

/** Control class for "Approve and present versioned challenge rules" (US-28 / GYM-31, FR-14.1, FR-14.5). */
public class ChallengePlanner {

    private final IChallengeStore store;
    private final IMemberLookup memberLookup;
    private final Clock clock;

    public ChallengePlanner(IChallengeStore store, IMemberLookup memberLookup, Clock clock) {
        this.store = Objects.requireNonNull(store);
        this.memberLookup = Objects.requireNonNull(memberLookup);
        this.clock = Objects.requireNonNull(clock);
    }

    /** Message 1 of the collaboration diagram. */
    public ChallengeRuleVersion approveRules(String ruleId, String trainerId) {
        ChallengeRuleVersion draft = store.findRuleVersion(ruleId)                       // 1.1
                .orElseThrow(() -> new IllegalArgumentException("Unknown rule " + ruleId));
        Optional<ChallengeRuleVersion> current =
                store.findApprovedRule(draft.getExercise(), draft.getLevel());           // 1.2
        Instant now = clock.instant();
        draft.approve(trainerId, now);                                                   // 1.3
        current.ifPresent(previous -> previous.supersede(now));                          // 1.4
        store.saveApproval(draft, current.orElse(null));                                 // 1.5
        return draft;
    }

    public ChallengeRuleVersion rejectRules(String ruleId, String trainerId, String reason) {
        ChallengeRuleVersion draft = store.findRuleVersion(ruleId)
                .orElseThrow(() -> new IllegalArgumentException("Unknown rule " + ruleId));
        draft.reject(trainerId, reason);
        store.saveRejection(draft);
        return draft;
    }

    /** Message 2 of the collaboration diagram (FR-14.5). */
    public RuleSummary presentRules(String memberId, String exercise) {
        if (!memberLookup.exists(memberId)) {                                            // 2.1
            throw new IllegalArgumentException("Unknown member " + memberId);
        }
        int level = store.findCurrentLevel(memberId, exercise)                           // 2.2
                .orElseThrow(() -> new IllegalStateException("No approved level for " + memberId));
        ChallengeRuleVersion rule = store.findApprovedRule(exercise, level)              // 2.3
                .orElseThrow(() -> new IllegalStateException("No approved rule for " + exercise + " level " + level));
        return rule.summary();                                                           // 2.4
    }
}
