package com.gymarena.member;

import java.util.Optional;

/** Member persistence port; realized by SqlMemberStore (gymarena_member). */
public interface IMemberStore {
    Optional<MemberProfile> findById(String memberId);
}
