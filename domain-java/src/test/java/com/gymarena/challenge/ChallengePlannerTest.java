package com.gymarena.challenge;

import static com.gymarena.challenge.ChallengeFixtures.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import java.time.Duration;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InOrder;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

/** Scenario "Approve and present versioned challenge rules": mocks = collaboration messages 1.x and 2.x. */
@ExtendWith(MockitoExtension.class)
class ChallengePlannerTest {

    @Mock IChallengeStore store;        // :SqlChallengeStore
    @Mock IMemberLookup memberLookup;   // :MemberProfileClient

    ChallengePlanner planner;
    ChallengeRuleVersion v3;
    ChallengeRuleVersion v4;

    @BeforeEach
    void setUp() {
        planner = new ChallengePlanner(store, memberLookup, CLOCK);
        v3 = approvedV3();
        v4 = draftV4();
    }

    @Test
    @DisplayName("TC-CHL-01: 1: approveRules sends 1.1 findRuleVersion, 1.2 findApprovedRule, 1.5 saveApproval in order")
    void TC_CHL_01_approveSupersedesPreviousVersion() {
        when(store.findRuleVersion(V4_ID)).thenReturn(Optional.of(v4));
        when(store.findApprovedRule("SQUAT", 2)).thenReturn(Optional.of(v3));

        ChallengeRuleVersion result = planner.approveRules(V4_ID, TRAINER);

        assertSame(v4, result);
        assertEquals(RuleStatus.APPROVED, v4.getStatus());          // 1.3 on fixture v4
        assertEquals(TRAINER, v4.getApprovedBy());
        assertEquals(NOW, v4.getApprovedAt());
        assertEquals(RuleStatus.SUPERSEDED, v3.getStatus());        // 1.4 on fixture v3
        InOrder order = inOrder(store);
        order.verify(store).findRuleVersion(V4_ID);
        order.verify(store).findApprovedRule("SQUAT", 2);
        order.verify(store).saveApproval(v4, v3);
        verifyNoMoreInteractions(store);
        verifyNoInteractions(memberLookup);
    }

    @Test
    @DisplayName("TC-CHL-02: First version for a level: nothing to supersede, saveApproval(v, null)")
    void TC_CHL_02_approveFirstVersion() {
        when(store.findRuleVersion(V4_ID)).thenReturn(Optional.of(v4));
        when(store.findApprovedRule("SQUAT", 2)).thenReturn(Optional.empty());

        planner.approveRules(V4_ID, TRAINER);

        verify(store).saveApproval(v4, null);
    }

    @Test
    @DisplayName("TC-CHL-03: Unknown rule id: stops after 1.1")
    void TC_CHL_03_unknownRule() {
        when(store.findRuleVersion("CR-404")).thenReturn(Optional.empty());

        assertThrows(IllegalArgumentException.class, () -> planner.approveRules("CR-404", TRAINER));
        verify(store, never()).saveApproval(any(), any());
    }

    @Test
    @DisplayName("TC-CHL-04: Approving an already approved version is refused; the current version is not superseded")
    void TC_CHL_04_approveTwice() {
        when(store.findRuleVersion(V3_ID)).thenReturn(Optional.of(v3));
        when(store.findApprovedRule("SQUAT", 2)).thenReturn(Optional.of(v3));

        assertThrows(IllegalStateException.class, () -> planner.approveRules(V3_ID, TRAINER));
        assertEquals(RuleStatus.APPROVED, v3.getStatus());
        verify(store, never()).saveApproval(any(), any());
    }

    @Test
    @DisplayName("TC-CHL-05: rejectRules marks the draft REJECTED and saves it")
    void TC_CHL_05_reject() {
        when(store.findRuleVersion(V4_ID)).thenReturn(Optional.of(v4));

        planner.rejectRules(V4_ID, TRAINER, "Target too high for level 2");

        assertEquals(RuleStatus.REJECTED, v4.getStatus());
        verify(store).saveRejection(v4);
    }

    @Test
    @DisplayName("TC-CHL-06: 2: presentRules sends 2.1 exists, 2.2 findCurrentLevel, 2.3 findApprovedRule, then 2.4 summary")
    void TC_CHL_06_presentRules() {
        v4.approve(TRAINER, NOW);                                   // state after message 1
        when(memberLookup.exists(MEMBER_ID)).thenReturn(true);
        when(store.findCurrentLevel(MEMBER_ID, "SQUAT")).thenReturn(Optional.of(2));
        when(store.findApprovedRule("SQUAT", 2)).thenReturn(Optional.of(v4));

        RuleSummary summary = planner.presentRules(MEMBER_ID, "SQUAT");

        assertEquals(new RuleSummary("SQUAT", 2, 4, 22, Duration.ofSeconds(120), 12, 3, WinnerRule.MOST_REPETITIONS),
                summary);
        InOrder order = inOrder(memberLookup, store);
        order.verify(memberLookup).exists(MEMBER_ID);
        order.verify(store).findCurrentLevel(MEMBER_ID, "SQUAT");
        order.verify(store).findApprovedRule("SQUAT", 2);
        verifyNoMoreInteractions(memberLookup, store);
    }

    @Test
    @DisplayName("TC-CHL-07: Unknown member: rules are not read")
    void TC_CHL_07_presentUnknownMember() {
        when(memberLookup.exists("MBR-9999")).thenReturn(false);

        assertThrows(IllegalArgumentException.class, () -> planner.presentRules("MBR-9999", "SQUAT"));
        verifyNoInteractions(store);
    }

    @Test
    @DisplayName("TC-CHL-08: Member without an approved level or level without approved rules")
    void TC_CHL_08_presentWithoutLevelOrRule() {
        when(memberLookup.exists(MEMBER_ID)).thenReturn(true);
        when(store.findCurrentLevel(MEMBER_ID, "SQUAT")).thenReturn(Optional.empty());
        assertThrows(IllegalStateException.class, () -> planner.presentRules(MEMBER_ID, "SQUAT"));

        when(store.findCurrentLevel(MEMBER_ID, "SQUAT")).thenReturn(Optional.of(3));
        when(store.findApprovedRule("SQUAT", 3)).thenReturn(Optional.empty());
        assertThrows(IllegalStateException.class, () -> planner.presentRules(MEMBER_ID, "SQUAT"));
    }

    @Test
    @DisplayName("TC-CHL-09: Reject an unknown rule; planner without store")
    void TC_CHL_09_rejectUnknownRuleAndNullCollaborators() {
        when(store.findRuleVersion("CR-404")).thenReturn(Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> planner.rejectRules("CR-404", TRAINER, "x"));
        assertThrows(NullPointerException.class, () -> new ChallengePlanner(null, memberLookup, CLOCK));
    }
}
