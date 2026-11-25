package com.gymarena.session;

/** Decides pause and resume for tracking problems (FR-06.1, FR-06.3). */
public class RecoveryPolicy {

    public boolean shouldPause(ChallengeSession session) {
        return session.getStatus() == SessionStatus.ACTIVE;
    }

    public boolean canResume(ChallengeSession session, boolean trackingReliable, boolean assignmentsConfirmed) {
        return session.getStatus() == SessionStatus.PAUSED && trackingReliable && assignmentsConfirmed;
    }
}
