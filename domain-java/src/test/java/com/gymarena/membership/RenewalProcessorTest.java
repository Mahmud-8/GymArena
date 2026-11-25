package com.gymarena.membership;

import static com.gymarena.membership.RenewalFixtures.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import java.time.LocalDate;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InOrder;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

/** Scenario "Record a membership renewal": mocks = collaboration diagram messages 1.1 to 1.5. */
@ExtendWith(MockitoExtension.class)
class RenewalProcessorTest {

    @Mock IMemberLookup memberLookup;      // :MemberProfileClient
    @Mock IMembershipStore store;          // :SqlMembershipStore
    @Mock IRenewalFeed renewalFeed;        // :RenewalOutbox

    RenewalProcessor processor;
    Membership m42;

    @BeforeEach
    void setUp() {
        processor = new RenewalProcessor(memberLookup, store, renewalFeed, CLOCK);
        m42 = activeMembership();
    }

    @Test
    @DisplayName("1: renew() sends 1.1 exists, 1.2 findByMemberId, 1.4 saveRenewal, 1.5 publish in order")
    void renewFollowsCollaborationMessages() {
        when(memberLookup.exists(MEMBER_ID)).thenReturn(true);
        when(store.findByMemberId(MEMBER_ID)).thenReturn(Optional.of(m42));

        RenewalRecord record = processor.renew(MEMBER_ID, REVISED_EXPIRY, STAFF_ID);

        assertEquals(expectedRecord(), record);
        assertEquals(REVISED_EXPIRY, m42.getExpiryDate());
        assertEquals(MembershipStatus.ACTIVE, m42.getStatus());

        InOrder order = inOrder(memberLookup, store, renewalFeed);
        order.verify(memberLookup).exists(MEMBER_ID);
        order.verify(store).findByMemberId(MEMBER_ID);
        order.verify(store).saveRenewal(m42, expectedRecord());
        order.verify(renewalFeed).publish(new RenewalChanged(MEMBER_ID, CURRENT_EXPIRY, REVISED_EXPIRY));
        verifyNoMoreInteractions(memberLookup, store, renewalFeed);
    }

    @Test
    @DisplayName("Renewing an expired membership makes it ACTIVE again and is published once")
    void renewExpiredMembership() {
        Membership expired = expiredMembership();
        when(memberLookup.exists(MEMBER_ID)).thenReturn(true);
        when(store.findByMemberId(MEMBER_ID)).thenReturn(Optional.of(expired));

        processor.renew(MEMBER_ID, REVISED_EXPIRY, STAFF_ID);

        assertEquals(MembershipStatus.ACTIVE, expired.getStatus());
        verify(renewalFeed, times(1)).publish(any());
    }

    @Test
    @DisplayName("Unknown member: stops after 1.1, nothing saved or published")
    void unknownMember() {
        when(memberLookup.exists("MBR-9999")).thenReturn(false);

        assertThrows(MemberNotFoundException.class,
                () -> processor.renew("MBR-9999", REVISED_EXPIRY, STAFF_ID));
        verifyNoInteractions(store, renewalFeed);
    }

    @Test
    @DisplayName("Member without a membership record is rejected before any save")
    void missingMembership() {
        when(memberLookup.exists(MEMBER_ID)).thenReturn(true);
        when(store.findByMemberId(MEMBER_ID)).thenReturn(Optional.empty());

        assertThrows(IllegalStateException.class,
                () -> processor.renew(MEMBER_ID, REVISED_EXPIRY, STAFF_ID));
        verify(store, never()).saveRenewal(any(), any());
        verifyNoInteractions(renewalFeed);
    }

    @Test
    @DisplayName("Invalid revised date: guard fails, no saveRenewal and no publish")
    void invalidRevisedDate() {
        when(memberLookup.exists(MEMBER_ID)).thenReturn(true);
        when(store.findByMemberId(MEMBER_ID)).thenReturn(Optional.of(m42));

        assertThrows(IllegalArgumentException.class,
                () -> processor.renew(MEMBER_ID, LocalDate.of(2026, 11, 1), STAFF_ID));
        assertEquals(CURRENT_EXPIRY, m42.getExpiryDate());
        verify(store, never()).saveRenewal(any(), any());
        verifyNoInteractions(renewalFeed);
    }

    @Test
    void constructorRejectsMissingCollaborators() {
        assertThrows(NullPointerException.class, () -> new RenewalProcessor(null, store, renewalFeed, CLOCK));
    }
}
