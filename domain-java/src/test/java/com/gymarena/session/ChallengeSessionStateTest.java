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
        @DisplayName("[*] -> CREATED on creation (FR-05.1)")
        void created() {
            ChallengeSession s = createdSession();
            assertEquals(SessionStatus.CREATED, s.getStatus());
            assertEquals(2, s.getParticipants().size());
            assertEquals(SessionMode.LOCAL_1V1, s.getMode());
            assertEquals(3, s.getRules().ruleVersion());
            assertEquals(SESSION_ID, s.getSessionId());
        }

        @Test
        @DisplayName("SOLO session with one member is valid")
        void solo() {
            ChallengeSession s = new ChallengeSession("SES-2001", SessionMode.SOLO, squatRules(),
                    List.of(new SessionParticipant(OMAR, "CENTER")));
            assertEquals(SessionStatus.CREATED, s.getStatus());
        }

        @Test
        @DisplayName("CREATED -> ACTIVE : start [all positions reliable]")
        void start() {
            ChallengeSession s = createdSession();
            s.start(true, STARTED_AT);
            assertEquals(SessionStatus.ACTIVE, s.getStatus());
        }

        @Test
        @DisplayName("ACTIVE -> PAUSED : trackingLost / stop timer, record interruption")
        void pause() {
            ChallengeSession s = pausedSession();
            assertEquals(SessionStatus.PAUSED, s.getStatus());
            assertEquals(Duration.ofSeconds(95), s.activeTime(RESUMED_AT));
            assertEquals("RIGHT", s.getInterruptions().get(0).position());
        }

        @Test
        @DisplayName("PAUSED -> ACTIVE : resume [reliable and confirmed]; paused time excluded (FR-06.2)")
        void resume() {
            ChallengeSession s = pausedSession();
            s.resume(true, true, RESUMED_AT);
            assertEquals(SessionStatus.ACTIVE, s.getStatus());
            assertEquals(Duration.ofSeconds(105), s.activeTime(RESUMED_AT.plusSeconds(10)));
        }

        @Test
        @DisplayName("ACTIVE -> COMPLETED : finish [all targets reached]")
        void completeByTargets() {
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
        @DisplayName("ACTIVE -> COMPLETED : finish [time limit reached]")
        void completeByTimeLimit() {
            ChallengeSession s = activeSession();
            s.complete(STARTED_AT.plusSeconds(120));
            assertEquals(SessionStatus.COMPLETED, s.getStatus());
            assertEquals(Duration.ofSeconds(120), s.activeTime(STARTED_AT.plusSeconds(500)));
        }

        @Test
        @DisplayName("ACTIVE -> STOPPED : reportDiscomfort")
        void stopFromActive() {
            ChallengeSession s = activeSession();
            s.stopForDiscomfort(LOST_AT);
            assertEquals(SessionStatus.STOPPED, s.getStatus());
            assertEquals(InterruptionReason.DISCOMFORT, s.getInterruptions().get(0).reason());
        }

        @Test
        @DisplayName("PAUSED -> STOPPED : reportDiscomfort")
        void stopFromPaused() {
            ChallengeSession s = pausedSession();
            s.stopForDiscomfort(RESUMED_AT);
            assertEquals(SessionStatus.STOPPED, s.getStatus());
            assertEquals(Duration.ofSeconds(95), s.activeTime(RESUMED_AT));
        }

        @Test
        @DisplayName("PAUSED -> INCOMPLETE : abandon [unresolved]")
        void incomplete() {
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
        @DisplayName("CREATED -x-> ACTIVE when tracking is unreliable (guard false)")
        void startUnreliable() {
            ChallengeSession s = createdSession();
            assertThrows(IllegalStateException.class, () -> s.start(false, STARTED_AT));
            assertEquals(SessionStatus.CREATED, s.getStatus());
        }

        @Test
        @DisplayName("ACTIVE -x-> start again")
        void startTwice() {
            assertThrows(IllegalStateException.class, () -> activeSession().start(true, LOST_AT));
        }

        @Test
        @DisplayName("CREATED -x-> PAUSED")
        void pauseBeforeStart() {
            assertThrows(IllegalStateException.class,
                    () -> createdSession().pause(InterruptionReason.TRACKING_LOST, "LEFT", STARTED_AT));
        }

        @Test
        @DisplayName("PAUSED -x-> ACTIVE without reliable tracking")
        void resumeUnreliable() {
            ChallengeSession s = pausedSession();
            assertThrows(IllegalStateException.class, () -> s.resume(false, true, RESUMED_AT));
            assertEquals(SessionStatus.PAUSED, s.getStatus());
        }

        @Test
        @DisplayName("PAUSED -x-> ACTIVE without confirmed positions")
        void resumeUnconfirmed() {
            assertThrows(IllegalStateException.class, () -> pausedSession().resume(true, false, RESUMED_AT));
        }

        @Test
        @DisplayName("ACTIVE -x-> resume")
        void resumeActive() {
            assertThrows(IllegalStateException.class, () -> activeSession().resume(true, true, LOST_AT));
        }

        @Test
        @DisplayName("ACTIVE -x-> COMPLETED before targets or time limit")
        void completeTooEarly() {
            ChallengeSession s = activeSession();
            assertThrows(IllegalStateException.class, () -> s.complete(LOST_AT));
            assertEquals(SessionStatus.ACTIVE, s.getStatus());
        }

        @Test
        @DisplayName("PAUSED -x-> COMPLETED")
        void completePaused() {
            assertThrows(IllegalStateException.class, () -> pausedSession().complete(RESUMED_AT));
        }

        @Test
        @DisplayName("PAUSED -x-> addRepetition (FR-02.5)")
        void countWhilePaused() {
            ChallengeSession s = pausedSession();
            assertThrows(IllegalStateException.class, () -> s.addRepetition(OMAR));
            assertEquals(14, s.participant(OMAR).getAcceptedRepetitions());
        }

        @Test
        @DisplayName("CREATED -x-> STOPPED")
        void stopCreated() {
            assertThrows(IllegalStateException.class, () -> createdSession().stopForDiscomfort(STARTED_AT));
        }

        @Test
        @DisplayName("COMPLETED -x-> STOPPED (final state)")
        void stopCompleted() {
            ChallengeSession s = activeSession();
            s.complete(STARTED_AT.plusSeconds(120));
            assertThrows(IllegalStateException.class, () -> s.stopForDiscomfort(STARTED_AT.plusSeconds(130)));
        }

        @Test
        @DisplayName("ACTIVE -x-> INCOMPLETE")
        void incompleteFromActive() {
            assertThrows(IllegalStateException.class, () -> activeSession().closeIncomplete());
        }

        @Test
        @DisplayName("INCOMPLETE -x-> resume (final state)")
        void resumeIncomplete() {
            ChallengeSession s = pausedSession();
            s.closeIncomplete();
            assertThrows(IllegalStateException.class, () -> s.resume(true, true, RESUMED_AT));
            assertFalse(SessionStatus.PAUSED.isFinal());
        }

        @Test
        @DisplayName("1v1 needs two distinct members; SOLO needs one")
        void participantRules() {
            assertThrows(IllegalArgumentException.class, () -> new ChallengeSession("S", SessionMode.LOCAL_1V1,
                    squatRules(), List.of(new SessionParticipant(OMAR, "LEFT"), new SessionParticipant(OMAR, "RIGHT"))));
            assertThrows(IllegalArgumentException.class, () -> new ChallengeSession("S", SessionMode.SOLO,
                    squatRules(), List.of(new SessionParticipant(OMAR, "LEFT"), new SessionParticipant(SARA, "RIGHT"))));
            assertThrows(IllegalArgumentException.class, () -> activeSession().addRepetition("MBR-0000"));
        }

        @Test
        @DisplayName("Rule snapshot rejects zero target and zero time")
        void ruleValidation() {
            assertThrows(IllegalArgumentException.class,
                    () -> new RuleSnapshot("SQUAT", 2, 0, Duration.ofSeconds(120), 3, true));
            assertThrows(IllegalArgumentException.class,
                    () -> new RuleSnapshot("SQUAT", 2, 20, Duration.ZERO, 3, true));
            assertThrows(IllegalArgumentException.class,
                    () -> new RuleSnapshot("SQUAT", 2, 20, Duration.ofSeconds(-5), 3, true));
        }

        @Test
        void activeTimeIsZeroBeforeStart() {
            assertEquals(Duration.ZERO, createdSession().activeTime(Instant.parse("2026-11-22T11:00:00Z")));
        }
    }
}
