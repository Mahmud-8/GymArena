package com.gymarena.session;

/** Narrow port to IExerciseTracking; realized by TrackingClient. */
public interface ITrackingControl {
    boolean isTrackingReliable(String sessionId);

    /** Stops counting and discards unfinished movement cycles (FR-02.4). */
    void pauseCounting(String sessionId);

    void resumeCounting(String sessionId);
}
