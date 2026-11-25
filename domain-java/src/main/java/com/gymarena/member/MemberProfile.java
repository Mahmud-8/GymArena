package com.gymarena.member;

import java.util.Objects;

/** Registered member (FR-09); mirrors member-service domain/models.py. */
public record MemberProfile(String memberId, String name, int age, String memberCode) {

    public MemberProfile {
        Objects.requireNonNull(memberId, "memberId");
        Objects.requireNonNull(name, "name");
        Objects.requireNonNull(memberCode, "memberCode");
    }
}
