package com.gymarena.challenge;

/** Narrow port to IMemberProfile; realized by MemberProfileClient. */
public interface IMemberLookup {
    boolean exists(String memberId);
}
