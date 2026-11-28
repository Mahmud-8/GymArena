package com.gymarena.challenge;

import static com.gymarena.challenge.ChallengeFixtures.*;
import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

/** One test per transition of the ChallengeRuleVersion state diagram, valid and invalid. */
class ChallengeRuleVersionStateTest {

    @Nested
    @DisplayName("Valid transitions")
    class Valid {

        @Test
        @DisplayName("TC-CHL-10: [*] -> DRAFT on creation")
        void TC_CHL_10_created() {
            ChallengeRuleVersion v4 = draftV4();
            assertEquals(RuleStatus.DRAFT, v4.getStatus());
            assertEquals(22, v4.getTargetRepetitions());
            assertEquals(Duration.ofSeconds(120), v4.getTimeAllowance());
            assertEquals(12, v4.getCompletionPoints());
            assertEquals(3, v4.getTimeoutDeduction());
            assertEquals(WinnerRule.MOST_REPETITIONS, v4.getWinnerRule());
            assertEquals(V4_ID, v4.getRuleId());
            assertEquals(4, v4.getVersion());
        }

        @Test
        @DisplayName("TC-CHL-11: DRAFT -> APPROVED : approve(trainerId) / approvedBy, approvedAt")
        void TC_CHL_11_approve() {
            ChallengeRuleVersion v4 = draftV4();
            v4.approve(TRAINER, NOW);
            assertEquals(RuleStatus.APPROVED, v4.getStatus());
            assertEquals(TRAINER, v4.getApprovedBy());
            assertEquals(NOW, v4.getApprovedAt());
        }

        @Test
        @DisplayName("TC-CHL-12: DRAFT -> REJECTED : reject(trainerId, reason)")
        void TC_CHL_12_reject() {
            ChallengeRuleVersion v4 = draftV4();
            v4.reject(TRAINER, "Target too high");
            assertEquals(RuleStatus.REJECTED, v4.getStatus());
            assertEquals("Target too high", v4.getRejectionReason());
            assertTrue(v4.getStatus().isFinal());
        }

        @Test
        @DisplayName("TC-CHL-13: APPROVED -> SUPERSEDED : supersede() [newer version approved]")
        void TC_CHL_13_supersede() {
            ChallengeRuleVersion v3 = approvedV3();
            v3.supersede(NOW);
            assertEquals(RuleStatus.SUPERSEDED, v3.getStatus());
            assertEquals(NOW, v3.getSupersededAt());
            assertTrue(v3.getStatus().isFinal());
        }

        @Test
        @DisplayName("TC-CHL-14: APPROVED : summary() shows target, time, reward, deduction and winner rule (FR-14.5)")
        void TC_CHL_14_summary() {
            RuleSummary s = approvedV3().summary();
            assertEquals(20, s.targetRepetitions());
            assertEquals(10, s.completionPoints());
            assertEquals(3, s.timeoutDeduction());
            assertFalse(RuleStatus.APPROVED.isFinal());
        }
    }

    @Nested
    @DisplayName("Invalid transitions")
    class Invalid {

        @Test
        @DisplayName("TC-CHL-15: APPROVED -x-> approve again")
        void TC_CHL_15_approveTwice() {
            assertThrows(IllegalStateException.class, () -> approvedV3().approve(TRAINER, NOW));
        }

        @Test
        @DisplayName("TC-CHL-16: DRAFT -x-> APPROVED without trainer (guard false)")
        void TC_CHL_16_approveWithoutTrainer() {
            ChallengeRuleVersion v4 = draftV4();
            assertThrows(IllegalArgumentException.class, () -> v4.approve(" ", NOW));
            assertEquals(RuleStatus.DRAFT, v4.getStatus());
        }

        @Test
        @DisplayName("TC-CHL-17: DRAFT -x-> REJECTED without reason (guard false)")
        void TC_CHL_17_rejectWithoutReason() {
            ChallengeRuleVersion v4 = draftV4();
            assertThrows(IllegalArgumentException.class, () -> v4.reject(TRAINER, ""));
            assertEquals(RuleStatus.DRAFT, v4.getStatus());
        }

        @Test
        @DisplayName("TC-CHL-18: APPROVED -x-> REJECTED")
        void TC_CHL_18_rejectApproved() {
            assertThrows(IllegalStateException.class, () -> approvedV3().reject(TRAINER, "late"));
        }

        @Test
        @DisplayName("TC-CHL-19: DRAFT -x-> SUPERSEDED")
        void TC_CHL_19_supersedeDraft() {
            assertThrows(IllegalStateException.class, () -> draftV4().supersede(NOW));
        }

        @Test
        @DisplayName("TC-CHL-20: REJECTED -x-> APPROVED (final state)")
        void TC_CHL_20_approveRejected() {
            ChallengeRuleVersion v4 = draftV4();
            v4.reject(TRAINER, "no");
            assertThrows(IllegalStateException.class, () -> v4.approve(TRAINER, NOW));
        }

        @Test
        @DisplayName("TC-CHL-21: SUPERSEDED -x-> summary (not shown to members)")
        void TC_CHL_21_summarySuperseded() {
            ChallengeRuleVersion v3 = approvedV3();
            v3.supersede(NOW);
            assertThrows(IllegalStateException.class, v3::summary);
        }

        @Test
        @DisplayName("TC-CHL-22: DRAFT -x-> summary")
        void TC_CHL_22_summaryDraft() {
            assertThrows(IllegalStateException.class, () -> draftV4().summary());
        }

        @ParameterizedTest(name = "[*] -x-> DRAFT for level {0}, version {1}, target {2}, seconds {3}, points {4}, deduction {5}")
        @CsvSource({"0, 1, 20, 120, 10, 3", "2, 0, 20, 120, 10, 3", "2, 4, 0, 120, 10, 3", "2, 4, 20, 0, 10, 3",
                    "2, 4, 20, -5, 10, 3", "2, 4, 20, 120, -1, 3", "2, 4, 20, 120, 10, -1"})
        @DisplayName("TC-CHL-23: Invalid: rule values (parameterized, 7 runs)")
        void TC_CHL_23_invalidCreation(int level, int version, int target, int seconds, int points, int deduction) {
            assertThrows(IllegalArgumentException.class, () -> new ChallengeRuleVersion("CR-X", "SQUAT", level,
                    version, target, Duration.ofSeconds(seconds), points, deduction, WinnerRule.FIRST_TO_TARGET));
        }

        @Test
        @DisplayName("TC-CHL-24: Invalid: missing rule id, time allowance or winner rule")
        void TC_CHL_24_missingFields() {
            assertThrows(IllegalArgumentException.class, () -> new ChallengeRuleVersion(null, "SQUAT", 2, 4, 20,
                    Duration.ofSeconds(120), 10, 3, WinnerRule.FIRST_TO_TARGET));
            assertThrows(NullPointerException.class, () -> new ChallengeRuleVersion("CR-X", "SQUAT", 2, 4, 20,
                    null, 10, 3, WinnerRule.FIRST_TO_TARGET));
            assertThrows(NullPointerException.class, () -> new ChallengeRuleVersion("CR-X", "SQUAT", 2, 4, 20,
                    Duration.ofSeconds(120), 10, 3, null));
        }
    }
}
