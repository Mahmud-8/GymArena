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
        @DisplayName("TC-MBS-07: [*] -> NO_SUBSCRIPTION on creation")
        void TC_MBS_07_initialState() {
            assertEquals(MembershipStatus.NO_SUBSCRIPTION, new Membership(MEMBER_ID, WHATSAPP).getStatus());
        }

        @Test
        @DisplayName("TC-MBS-08: NO_SUBSCRIPTION -> ACTIVE : recordSubscription [expiry >= today]")
        void TC_MBS_08_recordSubscription() {
            Membership m = new Membership(MEMBER_ID, WHATSAPP);
            m.recordSubscription(START, CURRENT_EXPIRY, TODAY);
            assertEquals(MembershipStatus.ACTIVE, m.getStatus());
            assertEquals(START, m.getStartDate());
            assertEquals(CURRENT_EXPIRY, m.getExpiryDate());
        }

        @Test
        @DisplayName("TC-MBS-09: ACTIVE -> EXPIRED : checkExpiry [expiry < today]")
        void TC_MBS_09_expire() {
            Membership m = activeMembership();
            assertEquals(MembershipStatus.EXPIRED, m.checkExpiry(LocalDate.of(2026, 12, 1)));
        }

        @Test
        @DisplayName("TC-MBS-10: ACTIVE stays ACTIVE : checkExpiry [expiry >= today]")
        void TC_MBS_10_notYetExpired() {
            assertEquals(MembershipStatus.ACTIVE, activeMembership().checkExpiry(TODAY));
        }

        @Test
        @DisplayName("TC-MBS-11: EXPIRED stays EXPIRED on checkExpiry")
        void TC_MBS_11_expiredStaysExpired() {
            assertEquals(MembershipStatus.EXPIRED, expiredMembership().checkExpiry(TODAY));
        }

        @Test
        @DisplayName("TC-MBS-12: ACTIVE -> ACTIVE : renew [revised > expiry] / create RenewalRecord")
        void TC_MBS_12_renewActive() {
            Membership m = activeMembership();
            RenewalRecord r = m.renew(REVISED_EXPIRY, STAFF_ID, NOW, TODAY);
            assertEquals(expectedRecord(), r);
            assertEquals(MembershipStatus.ACTIVE, m.getStatus());
        }

        @Test
        @DisplayName("TC-MBS-13: EXPIRED -> ACTIVE : renew [revised > expiry and revised >= today]")
        void TC_MBS_13_renewExpired() {
            Membership m = expiredMembership();
            m.renew(REVISED_EXPIRY, STAFF_ID, NOW, TODAY);
            assertEquals(MembershipStatus.ACTIVE, m.getStatus());
            assertEquals(REVISED_EXPIRY, m.getExpiryDate());
        }

        @Test
        @DisplayName("TC-MBS-14: Change the WhatsApp reminder number")
        void TC_MBS_14_changeWhatsappNumber() {
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
        @DisplayName("TC-MBS-15: NO_SUBSCRIPTION -x-> renew")
        void TC_MBS_15_renewWithoutSubscription() {
            Membership m = new Membership(MEMBER_ID, WHATSAPP);
            assertThrows(IllegalStateException.class, () -> m.renew(REVISED_EXPIRY, STAFF_ID, NOW, TODAY));
            assertEquals(MembershipStatus.NO_SUBSCRIPTION, m.getStatus());
        }

        @Test
        @DisplayName("TC-MBS-16: ACTIVE -x-> recordSubscription (already subscribed)")
        void TC_MBS_16_recordTwice() {
            Membership m = activeMembership();
            assertThrows(IllegalStateException.class, () -> m.recordSubscription(START, REVISED_EXPIRY, TODAY));
        }

        @Test
        @DisplayName("TC-MBS-17: recordSubscription guard: expiry before start")
        void TC_MBS_17_expiryBeforeStart() {
            Membership m = new Membership(MEMBER_ID, WHATSAPP);
            assertThrows(IllegalArgumentException.class,
                    () -> m.recordSubscription(CURRENT_EXPIRY, START, TODAY));
            assertEquals(MembershipStatus.NO_SUBSCRIPTION, m.getStatus());
        }

        @Test
        @DisplayName("TC-MBS-18: recordSubscription guard: already expired")
        void TC_MBS_18_alreadyExpired() {
            Membership m = new Membership(MEMBER_ID, WHATSAPP);
            assertThrows(IllegalArgumentException.class,
                    () -> m.recordSubscription(START, LocalDate.of(2026, 9, 1), TODAY));
        }

        @Test
        @DisplayName("TC-MBS-19: renew guard: revised expiry not after current expiry")
        void TC_MBS_19_renewNotLater() {
            Membership m = activeMembership();
            assertThrows(IllegalArgumentException.class,
                    () -> m.renew(CURRENT_EXPIRY, STAFF_ID, NOW, TODAY));
            assertEquals(CURRENT_EXPIRY, m.getExpiryDate());
        }

        @Test
        @DisplayName("TC-MBS-20: renew guard: EXPIRED renewed to a date still in the past")
        void TC_MBS_20_renewIntoPast() {
            Membership m = expiredMembership();
            assertThrows(IllegalArgumentException.class,
                    () -> m.renew(LocalDate.of(2026, 11, 15), STAFF_ID, NOW, TODAY));
            assertEquals(MembershipStatus.EXPIRED, m.getStatus());
        }

        @Test
        @DisplayName("TC-MBS-21: renew requires the staff identifier")
        void TC_MBS_21_renewWithoutStaff() {
            assertThrows(IllegalArgumentException.class,
                    () -> activeMembership().renew(REVISED_EXPIRY, " ", NOW, TODAY));
        }

        @Test
        @DisplayName("TC-MBS-22: Invalid: blank member id or WhatsApp number")
        void TC_MBS_22_blankMemberIdAndNumberRejected() {
            assertThrows(IllegalArgumentException.class, () -> new Membership(null, WHATSAPP));
            assertThrows(IllegalArgumentException.class, () -> activeMembership().changeWhatsappNumber(""));
        }

        @Test
        @DisplayName("TC-MBS-23: Invalid: renewal record with a missing field")
        void TC_MBS_23_renewalRecordRequiresAllFields() {
            assertThrows(NullPointerException.class,
                    () -> new RenewalRecord(MEMBER_ID, null, REVISED_EXPIRY, STAFF_ID, NOW));
        }
    }
}
