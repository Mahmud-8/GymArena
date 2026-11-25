package com.gymarena.session;

import java.time.Clock;
import java.util.Objects;

/** Control class for "Pause and resume a shared-camera attempt" (US-11 / GYM-40, FR-06). */
public class SessionLifecycle {

    private final ISessionStore store;
    private final ITrackingControl tracking;
    private final RecoveryPolicy recoveryPolicy;
    private final Clock clock;

    public SessionLifecycle(ISessionStore store, ITrackingControl tracking,
                            RecoveryPolicy recoveryPolicy, Clock clock) {
        this.store = Objects.requireNonNull(store);
        this.tracking = Objects.requireNonNull(tracking);
        this.recoveryPolicy = Objects.requireNonNull(recoveryPolicy);
        this.clock = Objects.requireNonNull(clock);
    }

    /** FR-05.3: start only when every assigned position is reliable. */
    public SessionStatus startSession(String sessionId) {
        ChallengeSession session = load(sessionId);
        session.start(tracking.isTrackingReliable(sessionId), clock.instant());
        store.save(session);
        return session.getStatus();
    }

    /** Message 1 of the collaboration diagram. */
    public SessionStatus onTrackingLost(String sessionId, String position) {
        ChallengeSession session = load(sessionId);                         // 1.1
        if (recoveryPolicy.shouldPause(session)) {                          // 1.2
            session.pause(InterruptionReason.TRACKING_LOST, position, clock.instant()); // 1.3
            tracking.pauseCounting(sessionId);                              // 1.4
            store.save(session);                                            // 1.5
        }
        return session.getStatus();
    }

    /** Message 2 of the collaboration diagram. */
    public SessionStatus confirmAssignments(String sessionId) {
        ChallengeSession session = load(sessionId);                         // 2.1
        boolean reliable = tracking.isTrackingReliable(sessionId);          // 2.2
        if (recoveryPolicy.canResume(session, reliable, true)) {            // 2.3
            session.resume(reliable, true, clock.instant());                // 2.4
            tracking.resumeCounting(sessionId);                             // 2.5
            store.save(session);                                            // 2.6
        }
        return session.getStatus();
    }

    /** FR-06.4. */
    public SessionStatus reportDiscomfort(String sessionId) {
        ChallengeSession session = load(sessionId);
        session.stopForDiscomfort(clock.instant());
        tracking.pauseCounting(sessionId);
        store.save(session);
        return session.getStatus();
    }

    private ChallengeSession load(String sessionId) {
        return store.findById(sessionId)
                .orElseThrow(() -> new IllegalArgumentException("Unknown session " + sessionId));
    }
}
