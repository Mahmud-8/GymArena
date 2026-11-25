package com.gymarena.member;

import static com.gymarena.member.MeasurementFixtures.*;
import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

/** One test per transition of the WeightReading state diagram, valid and invalid. */
class WeightReadingStateTest {

    @Nested
    @DisplayName("Valid transitions")
    class Valid {

        @Test
        @DisplayName("[*] -> PENDING_CONFIRMATION : capture [stable and 20..300 kg]")
        void capture() {
            assertEquals(ReadingStatus.PENDING_CONFIRMATION, pendingReading().getStatus());
        }

        @Test
        @DisplayName("PENDING_CONFIRMATION -> CONFIRMED : confirm [same member] / stamp confirmedAt")
        void confirm() {
            WeightReading r = pendingReading();
            r.confirm(MEMBER_ID, CONFIRMED_AT);
            assertEquals(ReadingStatus.CONFIRMED, r.getStatus());
            assertEquals(CONFIRMED_AT, r.getConfirmedAt());
        }

        @Test
        @DisplayName("PENDING_CONFIRMATION -> DISCARDED : reject")
        void reject() {
            WeightReading r = pendingReading();
            r.reject();
            assertEquals(ReadingStatus.DISCARDED, r.getStatus());
            assertNull(r.getConfirmedAt());
        }

        @ParameterizedTest(name = "boundary {0} kg is valid")
        @CsvSource({"20.0", "300.0"})
        void boundaries(double kg) {
            assertTrue(new ScaleReading(kg, true, READ_AT).isValid());
        }
    }

    @Nested
    @DisplayName("Invalid transitions")
    class Invalid {

        @ParameterizedTest(name = "[*] -x-> PENDING for {0} kg, stable={1}")
        @CsvSource({"78.4, false", "19.9, true", "300.1, true", "0.0, true"})
        void captureInvalid(double kg, boolean stable) {
            ScaleReading raw = new ScaleReading(kg, stable, READ_AT);
            assertThrows(InvalidScaleReadingException.class, () -> WeightReading.capture(READING_ID, omar(), raw));
        }

        @Test
        @DisplayName("PENDING -x-> CONFIRMED by another member (guard false)")
        void confirmOtherMember() {
            WeightReading r = pendingReading();
            assertThrows(IllegalArgumentException.class, () -> r.confirm("MBR-0057", CONFIRMED_AT));
            assertEquals(ReadingStatus.PENDING_CONFIRMATION, r.getStatus());
        }

        @Test
        @DisplayName("CONFIRMED -x-> confirm again")
        void confirmTwice() {
            WeightReading r = pendingReading();
            r.confirm(MEMBER_ID, CONFIRMED_AT);
            assertThrows(IllegalStateException.class, () -> r.confirm(MEMBER_ID, CONFIRMED_AT));
        }

        @Test
        @DisplayName("CONFIRMED -x-> DISCARDED")
        void rejectConfirmed() {
            WeightReading r = pendingReading();
            r.confirm(MEMBER_ID, CONFIRMED_AT);
            assertThrows(IllegalStateException.class, r::reject);
            assertEquals(ReadingStatus.CONFIRMED, r.getStatus());
        }

        @Test
        @DisplayName("DISCARDED -x-> CONFIRMED")
        void confirmDiscarded() {
            WeightReading r = pendingReading();
            r.reject();
            assertThrows(IllegalStateException.class, () -> r.confirm(MEMBER_ID, CONFIRMED_AT));
        }

        @Test
        void profileRequiresIds() {
            assertThrows(NullPointerException.class, () -> new MemberProfile(null, "Omar Adel", 24, "GA-7Q4K"));
        }
    }
}
