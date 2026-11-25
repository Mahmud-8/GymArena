package com.gymarena.session;

import static com.gymarena.session.SessionFixtures.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyBoolean;
import static org.mockito.Mockito.*;

import java.time.Duration;
import java.util.Optional;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InOrder;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

/** Scenario "Pause and resume a local 1v1 attempt": mocks = collaboration messages 1.x and 2.x. */
@ExtendWith(MockitoExtension.class)
class SessionLifecycleTest {

    @Mock ISessionStore store;           // :SqlSessionStore
    @Mock ITrackingControl tracking;     // :TrackingClient
    @Mock RecoveryPolicy recoveryPolicy; // :RecoveryPolicy

    @Test
    @DisplayName("1: onTrackingLost sends 1.1 findById, 1.2 shouldPause, 1.4 pauseCounting, 1.5 save")
    void trackingLostPausesSession() {
        ChallengeSession s1001 = activeSession();
        SessionLifecycle lifecycle = new SessionLifecycle(store, tracking, recoveryPolicy, clockAt(LOST_AT));
        when(store.findById(SESSION_ID)).thenReturn(Optional.of(s1001));
        when(recoveryPolicy.shouldPause(s1001)).thenReturn(true);

        SessionStatus status = lifecycle.onTrackingLost(SESSION_ID, "RIGHT");

        assertEquals(SessionStatus.PAUSED, status);
        assertEquals(Duration.ofSeconds(95), s1001.activeTime(RESUMED_AT));
        assertEquals(InterruptionReason.TRACKING_LOST, s1001.getInterruptions().get(0).reason());
        InOrder order = inOrder(store, recoveryPolicy, tracking);
        order.verify(store).findById(SESSION_ID);
        order.verify(recoveryPolicy).shouldPause(s1001);
        order.verify(tracking).pauseCounting(SESSION_ID);
        order.verify(store).save(s1001);
        verifyNoMoreInteractions(store, recoveryPolicy, tracking);
    }

    @Test
    @DisplayName("Tracking lost while already PAUSED: policy says no pause, nothing saved")
    void trackingLostWhilePaused() {
        ChallengeSession s1001 = pausedSession();
        SessionLifecycle lifecycle = new SessionLifecycle(store, tracking, recoveryPolicy, clockAt(RESUMED_AT));
        when(store.findById(SESSION_ID)).thenReturn(Optional.of(s1001));
        when(recoveryPolicy.shouldPause(s1001)).thenReturn(false);

        assertEquals(SessionStatus.PAUSED, lifecycle.onTrackingLost(SESSION_ID, "LEFT"));
        verify(store, never()).save(any());
        verifyNoInteractions(tracking);
    }

    @Test
    @DisplayName("2: confirmAssignments sends 2.1 findById, 2.2 isTrackingReliable, 2.3 canResume, 2.5 resumeCounting, 2.6 save")
    void confirmationResumesSession() {
        ChallengeSession s1001 = pausedSession();
        SessionLifecycle lifecycle = new SessionLifecycle(store, tracking, recoveryPolicy, clockAt(RESUMED_AT));
        when(store.findById(SESSION_ID)).thenReturn(Optional.of(s1001));
        when(tracking.isTrackingReliable(SESSION_ID)).thenReturn(true);
        when(recoveryPolicy.canResume(s1001, true, true)).thenReturn(true);

        assertEquals(SessionStatus.ACTIVE, lifecycle.confirmAssignments(SESSION_ID));

        InOrder order = inOrder(store, tracking, recoveryPolicy);
        order.verify(store).findById(SESSION_ID);
        order.verify(tracking).isTrackingReliable(SESSION_ID);
        order.verify(recoveryPolicy).canResume(s1001, true, true);
        order.verify(tracking).resumeCounting(SESSION_ID);
        order.verify(store).save(s1001);
        verifyNoMoreInteractions(store, tracking, recoveryPolicy);
    }

    @Test
    @DisplayName("Confirmation while tracking is still unreliable keeps the session PAUSED")
    void confirmationWithUnreliableTracking() {
        ChallengeSession s1001 = pausedSession();
        SessionLifecycle lifecycle = new SessionLifecycle(store, tracking, recoveryPolicy, clockAt(RESUMED_AT));
        when(store.findById(SESSION_ID)).thenReturn(Optional.of(s1001));
        when(tracking.isTrackingReliable(SESSION_ID)).thenReturn(false);
        when(recoveryPolicy.canResume(s1001, false, true)).thenReturn(false);

        assertEquals(SessionStatus.PAUSED, lifecycle.confirmAssignments(SESSION_ID));
        verify(tracking, never()).resumeCounting(any());
        verify(store, never()).save(any());
    }

    @Test
    @DisplayName("startSession starts only with reliable tracking and saves the session")
    void startSession() {
        ChallengeSession s1001 = createdSession();
        SessionLifecycle lifecycle = new SessionLifecycle(store, tracking, recoveryPolicy, clockAt(STARTED_AT));
        when(store.findById(SESSION_ID)).thenReturn(Optional.of(s1001));
        when(tracking.isTrackingReliable(SESSION_ID)).thenReturn(true);

        assertEquals(SessionStatus.ACTIVE, lifecycle.startSession(SESSION_ID));
        verify(store).save(s1001);
    }

    @Test
    @DisplayName("reportDiscomfort stops counting and closes the session as STOPPED")
    void reportDiscomfort() {
        ChallengeSession s1001 = activeSession();
        SessionLifecycle lifecycle = new SessionLifecycle(store, tracking, recoveryPolicy, clockAt(LOST_AT));
        when(store.findById(SESSION_ID)).thenReturn(Optional.of(s1001));

        assertEquals(SessionStatus.STOPPED, lifecycle.reportDiscomfort(SESSION_ID));
        verify(tracking).pauseCounting(SESSION_ID);
        verify(store).save(s1001);
    }

    @Test
    @DisplayName("Unknown session id is rejected without calling tracking")
    void unknownSession() {
        SessionLifecycle lifecycle = new SessionLifecycle(store, tracking, recoveryPolicy, clockAt(LOST_AT));
        when(store.findById("SES-404")).thenReturn(Optional.empty());

        assertThrows(IllegalArgumentException.class, () -> lifecycle.onTrackingLost("SES-404", "LEFT"));
        verifyNoInteractions(tracking, recoveryPolicy);
    }

    @Test
    @DisplayName("RecoveryPolicy decisions")
    void recoveryPolicyRules() {
        RecoveryPolicy policy = new RecoveryPolicy();
        assertTrue(policy.shouldPause(activeSession()));
        assertFalse(policy.shouldPause(pausedSession()));
        assertTrue(policy.canResume(pausedSession(), true, true));
        assertFalse(policy.canResume(pausedSession(), false, true));
        assertFalse(policy.canResume(pausedSession(), true, false));
        assertFalse(policy.canResume(activeSession(), true, true));
        verify(recoveryPolicy, never()).canResume(any(), anyBoolean(), anyBoolean());
    }
}
