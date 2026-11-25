package com.gymarena.membership;

public class MemberNotFoundException extends RuntimeException {
    public MemberNotFoundException(String memberId) {
        super("Unknown member " + memberId);
    }
}
