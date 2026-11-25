package com.gymarena.session;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;

/**
 * Solo or local 1v1 challenge attempt (FR-05, FR-06). Main object of the session
 * state diagram: CREATED -> ACTIVE <-> PAUSED -> COMPLETED | STOPPED | INCOMPLETE.
 */
public class ChallengeSession {

    private final String sessionId;
    private final SessionMode mode;
    private final RuleSnapshot rules;
    private final List<SessionParticipant> participants;
    private final List<SessionInterruption> interruptions = new ArrayList<>();
    private SessionStatus status = SessionStatus.CREATED;
    private Duration accumulatedActive = Duration.ZERO;
    private Instant activeSince;

    /** FR-05.1: one confirmed member for SOLO, two distinct members for LOCAL_1V1. */
    public ChallengeSession(String sessionId, SessionMode mode, RuleSnapshot rules,
                            List<SessionParticipant> participants) {
        this.sessionId = Objects.requireNonNull(sessionId, "sessionId");
        this.mode = Objects.requireNonNull(mode, "mode");
        this.rules = Objects.requireNonNull(rules, "rules");
        Objects.requireNonNull(participants, "participants");
        int expected = mode == SessionMode.SOLO ? 1 : 2;
        if (participants.size() != expected) {
            throw new IllegalArgumentException(mode + " needs exactly " + expected + " participant(s)");
        }
        HashSet<String> ids = new HashSet<>();
        for (SessionParticipant p : participants) {
            if (!ids.add(p.getMemberId())) {
                throw new IllegalArgumentException("Participants must be distinct members");
            }
        }
        this.participants = List.copyOf(participants);
    }

    /** FR-05.3: CREATED --start() [all positions reliable] / start timer--> ACTIVE. */
    public void start(boolean allPositionsReliable, Instant now) {
        requireStatus(SessionStatus.CREATED, "start");
        if (!allPositionsReliable) {
            throw new IllegalStateException("Cannot start: tracking is not reliable at every position");
        }
        status = SessionStatus.ACTIVE;
        activeSince = now;
    }

    /** FR-02.5: repetitions are accepted only while ACTIVE. */
    public void addRepetition(String memberId) {
        requireStatus(SessionStatus.ACTIVE, "addRepetition");
        participant(memberId).addRepetition();
    }

    /** FR-06.1: ACTIVE --trackingLost(position) / stop timer, record interruption--> PAUSED. */
    public void pause(InterruptionReason reason, String position, Instant now) {
        requireStatus(SessionStatus.ACTIVE, "pause");
        accumulatedActive = accumulatedActive.plus(Duration.between(activeSince, now));
        activeSince = null;
        interruptions.add(new SessionInterruption(reason, position, now));
        status = SessionStatus.PAUSED;
    }

    /** FR-06.3: PAUSED --resume() [reliable and assignments confirmed] / restart timer--> ACTIVE. */
    public void resume(boolean trackingReliable, boolean assignmentsConfirmed, Instant now) {
        requireStatus(SessionStatus.PAUSED, "resume");
        if (!trackingReliable || !assignmentsConfirmed) {
            throw new IllegalStateException("Cannot resume until tracking is reliable and positions are confirmed");
        }
        activeSince = now;
        status = SessionStatus.ACTIVE;
    }

    /** FR-05.5: ACTIVE --finish() [all targets reached or time limit reached]--> COMPLETED. */
    public void complete(Instant now) {
        requireStatus(SessionStatus.ACTIVE, "complete");
        if (!allTargetsReached() && activeTime(now).compareTo(rules.timeLimit()) < 0) {
            throw new IllegalStateException("Targets not reached and time limit not expired");
        }
        accumulatedActive = accumulatedActive.plus(Duration.between(activeSince, now));
        activeSince = null;
        status = SessionStatus.COMPLETED;
    }

    /** FR-06.4: ACTIVE or PAUSED --reportDiscomfort()--> STOPPED (no scoring penalty). */
    public void stopForDiscomfort(Instant now) {
        if (status != SessionStatus.ACTIVE && status != SessionStatus.PAUSED) {
            throw new IllegalStateException("Cannot stop a session in state " + status);
        }
        if (status == SessionStatus.ACTIVE) {
            accumulatedActive = accumulatedActive.plus(Duration.between(activeSince, now));
            activeSince = null;
        }
        interruptions.add(new SessionInterruption(InterruptionReason.DISCOMFORT, null, now));
        status = SessionStatus.STOPPED;
    }

    /** FR-06.5: PAUSED --abandon() [tracking or identity unresolved]--> INCOMPLETE. */
    public void closeIncomplete() {
        requireStatus(SessionStatus.PAUSED, "closeIncomplete");
        status = SessionStatus.INCOMPLETE;
    }

    /** FR-06.2: active time excludes every paused interval. */
    public Duration activeTime(Instant now) {
        if (activeSince == null) {
            return accumulatedActive;
        }
        return accumulatedActive.plus(Duration.between(activeSince, now));
    }

    public boolean allTargetsReached() {
        return participants.stream().allMatch(p -> p.getAcceptedRepetitions() >= rules.targetRepetitions());
    }

    public SessionParticipant participant(String memberId) {
        return participants.stream()
                .filter(p -> p.getMemberId().equals(memberId))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Not a participant: " + memberId));
    }

    private void requireStatus(SessionStatus required, String operation) {
        if (status != required) {
            throw new IllegalStateException("Cannot " + operation + " a session in state " + status);
        }
    }

    public String getSessionId() { return sessionId; }
    public SessionMode getMode() { return mode; }
    public RuleSnapshot getRules() { return rules; }
    public List<SessionParticipant> getParticipants() { return participants; }
    public List<SessionInterruption> getInterruptions() { return Collections.unmodifiableList(interruptions); }
    public SessionStatus getStatus() { return status; }
}
