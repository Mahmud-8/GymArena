package com.gymarena.membership;

import static com.gymarena.membership.RenewalFixtures.*;
import static org.junit.jupiter.api.Assertions.*;

import java.time.LocalDate;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

/** One test per transition of the Membership state diagram, valid and invalid. */
class MembershipStateTest {

    @Nested
    @DisplayName("Valid transitions")
    class Valid {

        @Test
        @DisplayName("[*] -> NO_SUBSCRIPTION on creation")
        void initialState() {
            assertEquals(MembershipStatus.NO_SUBSCRIPTION, new Membership(MEMBER_ID, WHATSAPP).getStatus());
        }

        @Test
        @DisplayName("NO_SUBSCRIPTION -> ACTIVE : recordSubscription [expiry >= today]")
        void recordSubscription() {
            Membership m = new Membership(MEMBER_ID, WHATSAPP);
            m.recordSubscription(START, CURRENT_EXPIRY, TODAY);
            assertEquals(MembershipStatus.ACTIVE, m.getStatus());
            assertEquals(START, m.getStartDate());
            assertEquals(CURRENT_EXPIRY, m.getExpiryDate());
        }

        @Test
        @DisplayName("ACTIVE -> EXPIRED : checkExpiry [expiry < today]")
        void expire() {
            Membership m = activeMembership();
            assertEquals(MembershipStatus.EXPIRED, m.checkExpiry(LocalDate.of(2026, 12, 1)));
        }

        @Test
        @DisplayName("ACTIVE stays ACTIVE : checkExpiry [expiry >= today]")
        void notYetExpired() {
            assertEquals(MembershipStatus.ACTIVE, activeMembership().checkExpiry(TODAY));
        }

        @Test
        @DisplayName("EXPIRED stays EXPIRED on checkExpiry")
        void expiredStaysExpired() {
            assertEquals(MembershipStatus.EXPIRED, expiredMembership().checkExpiry(TODAY));
        }

        @Test
        @DisplayName("ACTIVE -> ACTIVE : renew [revised > expiry] / create RenewalRecord")
        void renewActive() {
            Membership m = activeMembership();
            RenewalRecord r = m.renew(REVISED_EXPIRY, STAFF_ID, NOW, TODAY);
            assertEquals(expectedRecord(), r);
            assertEquals(MembershipStatus.ACTIVE, m.getStatus());
        }

        @Test
        @DisplayName("EXPIRED -> ACTIVE : renew [revised > expiry and revised >= today]")
        void renewExpired() {
            Membership m = expiredMembership();
            m.renew(REVISED_EXPIRY, STAFF_ID, NOW, TODAY);
            assertEquals(MembershipStatus.ACTIVE, m.getStatus());
            assertEquals(REVISED_EXPIRY, m.getExpiryDate());
        }

        @Test
        void changeWhatsappNumber() {
            Membership m = activeMembership();
            m.changeWhatsappNumber("+201000000099");
            assertEquals("+201000000099", m.getWhatsappNumber());
            assertEquals(MEMBER_ID, m.getMemberId());
        }
    }

    @Nested
    @DisplayName("Invalid transitions")
    class Invalid {

        @Test
        @DisplayName("NO_SUBSCRIPTION -x-> renew")
        void renewWithoutSubscription() {
            Membership m = new Membership(MEMBER_ID, WHATSAPP);
            assertThrows(IllegalStateException.class, () -> m.renew(REVISED_EXPIRY, STAFF_ID, NOW, TODAY));
            assertEquals(MembershipStatus.NO_SUBSCRIPTION, m.getStatus());
        }

        @Test
        @DisplayName("ACTIVE -x-> recordSubscription (already subscribed)")
        void recordTwice() {
            Membership m = activeMembership();
            assertThrows(IllegalStateException.class, () -> m.recordSubscription(START, REVISED_EXPIRY, TODAY));
        }

        @Test
        @DisplayName("recordSubscription guard: expiry before start")
        void expiryBeforeStart() {
            Membership m = new Membership(MEMBER_ID, WHATSAPP);
            assertThrows(IllegalArgumentException.class,
                    () -> m.recordSubscription(CURRENT_EXPIRY, START, TODAY));
            assertEquals(MembershipStatus.NO_SUBSCRIPTION, m.getStatus());
        }

        @Test
        @DisplayName("recordSubscription guard: already expired")
        void alreadyExpired() {
            Membership m = new Membership(MEMBER_ID, WHATSAPP);
            assertThrows(IllegalArgumentException.class,
                    () -> m.recordSubscription(START, LocalDate.of(2026, 9, 1), TODAY));
        }

        @Test
        @DisplayName("renew guard: revised expiry not after current expiry")
        void renewNotLater() {
            Membership m = activeMembership();
            assertThrows(IllegalArgumentException.class,
                    () -> m.renew(CURRENT_EXPIRY, STAFF_ID, NOW, TODAY));
            assertEquals(CURRENT_EXPIRY, m.getExpiryDate());
        }

        @Test
        @DisplayName("renew guard: EXPIRED renewed to a date still in the past")
        void renewIntoPast() {
            Membership m = expiredMembership();
            assertThrows(IllegalArgumentException.class,
                    () -> m.renew(LocalDate.of(2026, 11, 15), STAFF_ID, NOW, TODAY));
            assertEquals(MembershipStatus.EXPIRED, m.getStatus());
        }

        @Test
        @DisplayName("renew requires the staff identifier")
        void renewWithoutStaff() {
            assertThrows(IllegalArgumentException.class,
                    () -> activeMembership().renew(REVISED_EXPIRY, " ", NOW, TODAY));
        }

        @Test
        void blankMemberIdAndNumberRejected() {
            assertThrows(IllegalArgumentException.class, () -> new Membership(null, WHATSAPP));
            assertThrows(IllegalArgumentException.class, () -> activeMembership().changeWhatsappNumber(""));
        }

        @Test
        void renewalRecordRequiresAllFields() {
            assertThrows(NullPointerException.class,
                    () -> new RenewalRecord(MEMBER_ID, null, REVISED_EXPIRY, STAFF_ID, NOW));
        }
    }
}
