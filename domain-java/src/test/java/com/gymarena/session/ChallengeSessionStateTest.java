package com.gymarena.session;

import static com.gymarena.session.SessionFixtures.*;
import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

/** One test per transition of the ChallengeSession state diagram, valid and invalid. */
class ChallengeSessionStateTest {

    @Nested
    @DisplayName("Valid transitions")
    class Valid {

        @Test
        @DisplayName("TC-SES-09: [*] -> CREATED on creation (FR-05.1)")
        void TC_SES_09_created() {
            ChallengeSession s = createdSession();
            assertEquals(SessionStatus.CREATED, s.getStatus());
            assertEquals(2, s.getParticipants().size());
            assertEquals(SessionMode.LOCAL_1V1, s.getMode());
            assertEquals(3, s.getRules().ruleVersion());
            assertEquals(SESSION_ID, s.getSessionId());
            assertEquals("LEFT", s.getParticipants().get(0).getPosition());
            assertEquals("RIGHT", s.getParticipants().get(1).getPosition());
        }

        @Test
        @DisplayName("TC-SES-10: SOLO session with one member is valid")
        void TC_SES_10_solo() {
            ChallengeSession s = new ChallengeSession("SES-2001", SessionMode.SOLO, squatRules(),
                    List.of(new SessionParticipant(OMAR, "CENTER")));
            assertEquals(SessionStatus.CREATED, s.getStatus());
        }

        @Test
        @DisplayName("TC-SES-11: CREATED -> ACTIVE : start [all positions reliable]")
        void TC_SES_11_start() {
            ChallengeSession s = createdSession();
            s.start(true, STARTED_AT);
            assertEquals(SessionStatus.ACTIVE, s.getStatus());
        }

        @Test
        @DisplayName("TC-SES-12: ACTIVE -> PAUSED : trackingLost / stop timer, record interruption")
        void TC_SES_12_pause() {
            ChallengeSession s = pausedSession();
            assertEquals(SessionStatus.PAUSED, s.getStatus());
            assertEquals(Duration.ofSeconds(95), s.activeTime(RESUMED_AT));
            assertEquals("RIGHT", s.getInterruptions().get(0).position());
        }

        @Test
        @DisplayName("TC-SES-13: PAUSED -> ACTIVE : resume [reliable and confirmed]; paused time excluded (FR-06.2)")
        void TC_SES_13_resume() {
            ChallengeSession s = pausedSession();
            s.resume(true, true, RESUMED_AT);
            assertEquals(SessionStatus.ACTIVE, s.getStatus());
            assertEquals(Duration.ofSeconds(105), s.activeTime(RESUMED_AT.plusSeconds(10)));
        }

        @Test
        @DisplayName("TC-SES-14: ACTIVE -> COMPLETED : finish [all targets reached]")
        void TC_SES_14_completeByTargets() {
            ChallengeSession s = activeSession();
            for (int i = 0; i < 6; i++) {
                s.addRepetition(OMAR);
            }
            for (int i = 0; i < 8; i++) {
                s.addRepetition(SARA);
            }
            assertTrue(s.allTargetsReached());
            s.complete(LOST_AT);
            assertEquals(SessionStatus.COMPLETED, s.getStatus());
            assertTrue(s.getStatus().isFinal());
            assertEquals(20, s.participant(SARA).getAcceptedRepetitions());
        }

        @Test
        @DisplayName("TC-SES-15: ACTIVE -> COMPLETED : finish [time limit reached]")
        void TC_SES_15_completeByTimeLimit() {
            ChallengeSession s = activeSession();
            s.complete(STARTED_AT.plusSeconds(120));
            assertEquals(SessionStatus.COMPLETED, s.getStatus());
            assertEquals(Duration.ofSeconds(120), s.activeTime(STARTED_AT.plusSeconds(500)));
        }

        @Test
        @DisplayName("TC-SES-16: ACTIVE -> STOPPED : reportDiscomfort")
        void TC_SES_16_stopFromActive() {
            ChallengeSession s = activeSession();
            s.stopForDiscomfort(LOST_AT);
            assertEquals(SessionStatus.STOPPED, s.getStatus());
            assertTrue(s.getStatus().isFinal());
            assertEquals(InterruptionReason.DISCOMFORT, s.getInterruptions().get(0).reason());
        }

        @Test
        @DisplayName("TC-SES-17: PAUSED -> STOPPED : reportDiscomfort")
        void TC_SES_17_stopFromPaused() {
            ChallengeSession s = pausedSession();
            s.stopForDiscomfort(RESUMED_AT);
            assertEquals(SessionStatus.STOPPED, s.getStatus());
            assertEquals(Duration.ofSeconds(95), s.activeTime(RESUMED_AT));
        }

        @Test
        @DisplayName("TC-SES-18: PAUSED -> INCOMPLETE : abandon [unresolved]")
        void TC_SES_18_incomplete() {
            ChallengeSession s = pausedSession();
            s.closeIncomplete();
            assertEquals(SessionStatus.INCOMPLETE, s.getStatus());
            assertTrue(s.getStatus().isFinal());
        }
    }

    @Nested
    @DisplayName("Invalid transitions")
    class Invalid {

        @Test
        @DisplayName("TC-SES-19: CREATED -x-> ACTIVE when tracking is unreliable (guard false)")
        void TC_SES_19_startUnreliable() {
            ChallengeSession s = createdSession();
            assertThrows(IllegalStateException.class, () -> s.start(false, STARTED_AT));
            assertEquals(SessionStatus.CREATED, s.getStatus());
        }

        @Test
        @DisplayName("TC-SES-20: ACTIVE -x-> start again")
        void TC_SES_20_startTwice() {
            assertThrows(IllegalStateException.class, () -> activeSession().start(true, LOST_AT));
        }

        @Test
        @DisplayName("TC-SES-21: CREATED -x-> PAUSED")
        void TC_SES_21_pauseBeforeStart() {
            assertThrows(IllegalStateException.class,
                    () -> createdSession().pause(InterruptionReason.TRACKING_LOST, "LEFT", STARTED_AT));
        }

        @Test
        @DisplayName("TC-SES-22: PAUSED -x-> ACTIVE without reliable tracking")
        void TC_SES_22_resumeUnreliable() {
            ChallengeSession s = pausedSession();
            assertThrows(IllegalStateException.class, () -> s.resume(false, true, RESUMED_AT));
            assertEquals(SessionStatus.PAUSED, s.getStatus());
        }

        @Test
        @DisplayName("TC-SES-23: PAUSED -x-> ACTIVE without confirmed positions")
        void TC_SES_23_resumeUnconfirmed() {
            assertThrows(IllegalStateException.class, () -> pausedSession().resume(true, false, RESUMED_AT));
        }

        @Test
        @DisplayName("TC-SES-24: ACTIVE -x-> resume")
        void TC_SES_24_resumeActive() {
            assertThrows(IllegalStateException.class, () -> activeSession().resume(true, true, LOST_AT));
        }

        @Test
        @DisplayName("TC-SES-25: ACTIVE -x-> COMPLETED before targets or time limit")
        void TC_SES_25_completeTooEarly() {
            ChallengeSession s = activeSession();
            assertThrows(IllegalStateException.class, () -> s.complete(LOST_AT));
            assertEquals(SessionStatus.ACTIVE, s.getStatus());
        }

        @Test
        @DisplayName("TC-SES-26: PAUSED -x-> COMPLETED")
        void TC_SES_26_completePaused() {
            assertThrows(IllegalStateException.class, () -> pausedSession().complete(RESUMED_AT));
        }

        @Test
        @DisplayName("TC-SES-27: PAUSED -x-> addRepetition (FR-02.5)")
        void TC_SES_27_countWhilePaused() {
            ChallengeSession s = pausedSession();
            assertThrows(IllegalStateException.class, () -> s.addRepetition(OMAR));
            assertEquals(14, s.participant(OMAR).getAcceptedRepetitions());
        }

        @Test
        @DisplayName("TC-SES-28: CREATED -x-> STOPPED")
        void TC_SES_28_stopCreated() {
            assertThrows(IllegalStateException.class, () -> createdSession().stopForDiscomfort(STARTED_AT));
        }

        @Test
        @DisplayName("TC-SES-29: COMPLETED -x-> STOPPED (final state)")
        void TC_SES_29_stopCompleted() {
            ChallengeSession s = activeSession();
            s.complete(STARTED_AT.plusSeconds(120));
            assertThrows(IllegalStateException.class, () -> s.stopForDiscomfort(STARTED_AT.plusSeconds(130)));
        }

        @Test
        @DisplayName("TC-SES-30: ACTIVE -x-> INCOMPLETE")
        void TC_SES_30_incompleteFromActive() {
            assertThrows(IllegalStateException.class, () -> activeSession().closeIncomplete());
        }

        @Test
        @DisplayName("TC-SES-31: INCOMPLETE -x-> resume (final state)")
        void TC_SES_31_resumeIncomplete() {
            ChallengeSession s = pausedSession();
            s.closeIncomplete();
            assertThrows(IllegalStateException.class, () -> s.resume(true, true, RESUMED_AT));
            assertFalse(SessionStatus.PAUSED.isFinal());
        }

        @Test
        @DisplayName("TC-SES-32: 1v1 needs two distinct members; SOLO needs one")
        void TC_SES_32_participantRules() {
            assertThrows(IllegalArgumentException.class, () -> new ChallengeSession("S", SessionMode.LOCAL_1V1,
                    squatRules(), List.of(new SessionParticipant(OMAR, "LEFT"), new SessionParticipant(OMAR, "RIGHT"))));
            assertThrows(IllegalArgumentException.class, () -> new ChallengeSession("S", SessionMode.SOLO,
                    squatRules(), List.of(new SessionParticipant(OMAR, "LEFT"), new SessionParticipant(SARA, "RIGHT"))));
            assertThrows(IllegalArgumentException.class, () -> activeSession().addRepetition("MBR-0000"));
        }

        @Test
        @DisplayName("TC-SES-33: Rule snapshot rejects zero target and zero time")
        void TC_SES_33_ruleValidation() {
            assertThrows(IllegalArgumentException.class,
                    () -> new RuleSnapshot("SQUAT", 2, 0, Duration.ofSeconds(120), 3, true));
            assertThrows(IllegalArgumentException.class,
                    () -> new RuleSnapshot("SQUAT", 2, 20, Duration.ZERO, 3, true));
            assertThrows(IllegalArgumentException.class,
                    () -> new RuleSnapshot("SQUAT", 2, 20, Duration.ofSeconds(-5), 3, true));
        }

        @Test
        @DisplayName("TC-SES-34: Active timer before the session starts")
        void TC_SES_34_activeTimeIsZeroBeforeStart() {
            assertEquals(Duration.ZERO, createdSession().activeTime(Instant.parse("2026-11-22T11:00:00Z")));
        }
    }
}
