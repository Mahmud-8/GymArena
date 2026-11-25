package com.gymarena.session;

import java.util.Optional;

/** Persistence port; realized by SqlSessionStore (gymarena_session). */
public interface ISessionStore {
    Optional<ChallengeSession> findById(String sessionId);

    void save(ChallengeSession session);
}
