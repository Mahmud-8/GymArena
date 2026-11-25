package com.gymarena.session;

import java.util.Objects;

/** A confirmed member at an assigned camera position. */
public class SessionParticipant {

    private final String memberId;
    private final String position;
    private int acceptedRepetitions;

    public SessionParticipant(String memberId, String position) {
        this.memberId = Objects.requireNonNull(memberId, "memberId");
        this.position = Objects.requireNonNull(position, "position");
    }

    void addRepetition() {
        acceptedRepetitions++;
    }

    public String getMemberId() { return memberId; }
    public String getPosition() { return position; }
    public int getAcceptedRepetitions() { return acceptedRepetitions; }
}
