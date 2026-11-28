package com.gymarena.member;

import static com.gymarena.member.MeasurementFixtures.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InOrder;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

/** Scenario "Capture and confirm a scale reading": mocks = collaboration messages 1.x and 2.x. */
@ExtendWith(MockitoExtension.class)
class MeasurementServiceTest {

    @Mock IMemberStore memberStore;           // :SqlMemberStore (members)
    @Mock IMeasurementStore measurementStore; // :SqlMemberStore (weight_measurements)
    @Mock IScaleSource scale;                 // :SerialScaleAdapter

    MeasurementService service;

    @BeforeEach
    void setUp() {
        service = new MeasurementService(memberStore, measurementStore, scale, CLOCK);
    }

    @Test
    @DisplayName("TC-MEM-01: 1: captureReading sends 1.1 findById, 1.2 readStableWeight, 1.3 nextReadingId, 1.5 save")
    void TC_MEM_01_captureStableReading() {
        when(memberStore.findById(MEMBER_ID)).thenReturn(Optional.of(omar()));
        when(scale.readStableWeight()).thenReturn(stableReading());
        when(measurementStore.nextReadingId()).thenReturn(READING_ID);

        WeightReading wr310 = service.captureReading(MEMBER_ID);

        assertEquals(READING_ID, wr310.getReadingId());
        assertEquals(78.4, wr310.getWeightKg());
        assertEquals(ReadingStatus.PENDING_CONFIRMATION, wr310.getStatus());
        InOrder order = inOrder(memberStore, scale, measurementStore);
        order.verify(memberStore).findById(MEMBER_ID);
        order.verify(scale).readStableWeight();
        order.verify(measurementStore).nextReadingId();
        order.verify(measurementStore).save(wr310);
        verifyNoMoreInteractions(memberStore, scale, measurementStore);
    }

    @Test
    @DisplayName("TC-MEM-02: FR-10.4: unstable reading is reported and nothing is saved")
    void TC_MEM_02_unstableReadingNotSaved() {
        when(memberStore.findById(MEMBER_ID)).thenReturn(Optional.of(omar()));
        when(scale.readStableWeight()).thenReturn(new ScaleReading(78.9, false, READ_AT));
        when(measurementStore.nextReadingId()).thenReturn(READING_ID);

        assertThrows(InvalidScaleReadingException.class, () -> service.captureReading(MEMBER_ID));
        verify(measurementStore, never()).save(any());
    }

    @Test
    @DisplayName("TC-MEM-03: Unknown member: the scale is never read")
    void TC_MEM_03_unknownMember() {
        when(memberStore.findById("MBR-9999")).thenReturn(Optional.empty());

        assertThrows(IllegalArgumentException.class, () -> service.captureReading("MBR-9999"));
        verifyNoInteractions(scale, measurementStore);
    }

    @Test
    @DisplayName("TC-MEM-04: 2: confirmReading sends 2.1 findById, 2.2 confirm, 2.3 save")
    void TC_MEM_04_confirmReading() {
        WeightReading wr310 = pendingReading();
        when(measurementStore.findById(READING_ID)).thenReturn(Optional.of(wr310));

        WeightReading result = service.confirmReading(READING_ID, MEMBER_ID);

        assertSame(wr310, result);
        assertEquals(ReadingStatus.CONFIRMED, wr310.getStatus());
        assertEquals(CONFIRMED_AT, wr310.getConfirmedAt());
        ArgumentCaptor<WeightReading> saved = ArgumentCaptor.forClass(WeightReading.class);
        InOrder order = inOrder(measurementStore);
        order.verify(measurementStore).findById(READING_ID);
        order.verify(measurementStore).save(saved.capture());
        assertEquals(ReadingStatus.CONFIRMED, saved.getValue().getStatus());
        verifyNoInteractions(scale, memberStore);
    }

    @Test
    @DisplayName("TC-MEM-05: Confirmation by another member is refused and not saved")
    void TC_MEM_05_confirmByOtherMember() {
        when(measurementStore.findById(READING_ID)).thenReturn(Optional.of(pendingReading()));

        assertThrows(IllegalArgumentException.class, () -> service.confirmReading(READING_ID, "MBR-0057"));
        verify(measurementStore, never()).save(any());
    }

    @Test
    @DisplayName("TC-MEM-06: rejectReading discards the pending reading and saves it")
    void TC_MEM_06_rejectReading() {
        WeightReading wr310 = pendingReading();
        when(measurementStore.findById(READING_ID)).thenReturn(Optional.of(wr310));

        assertEquals(ReadingStatus.DISCARDED, service.rejectReading(READING_ID).getStatus());
        verify(measurementStore).save(wr310);
    }

    @Test
    @DisplayName("TC-MEM-07: Unknown reading id")
    void TC_MEM_07_unknownReading() {
        when(measurementStore.findById("WR-404")).thenReturn(Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> service.confirmReading("WR-404", MEMBER_ID));
    }

    @Test
    @DisplayName("TC-MEM-08: Reading keeps the scale timestamp and member")
    void TC_MEM_08_readingKeepsScaleTimestamp() {
        assertEquals(Instant.parse("2026-11-22T09:40:12Z"), pendingReading().getReadAt());
        assertEquals(MEMBER_ID, pendingReading().getMemberId());
    }
}
