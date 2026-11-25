package com.gymarena.member;

import java.time.Clock;
import java.util.Objects;

/** Control class for "Capture and confirm an automatic scale reading" (US-19 / GYM-26, FR-10). */
public class MeasurementService {

    private final IMemberStore memberStore;
    private final IMeasurementStore measurementStore;
    private final IScaleSource scale;
    private final Clock clock;

    public MeasurementService(IMemberStore memberStore, IMeasurementStore measurementStore,
                              IScaleSource scale, Clock clock) {
        this.memberStore = Objects.requireNonNull(memberStore);
        this.measurementStore = Objects.requireNonNull(measurementStore);
        this.scale = Objects.requireNonNull(scale);
        this.clock = Objects.requireNonNull(clock);
    }

    /** Message 1 of the collaboration diagram. */
    public WeightReading captureReading(String memberId) {
        MemberProfile member = memberStore.findById(memberId)                 // 1.1
                .orElseThrow(() -> new IllegalArgumentException("Unknown member " + memberId));
        ScaleReading raw = scale.readStableWeight();                          // 1.2
        String readingId = measurementStore.nextReadingId();                  // 1.3
        WeightReading reading = WeightReading.capture(readingId, member, raw);  // 1.4 <<create>>
        measurementStore.save(reading);                                       // 1.5
        return reading;
    }

    /** Message 2 of the collaboration diagram. */
    public WeightReading confirmReading(String readingId, String memberId) {
        WeightReading reading = load(readingId);                              // 2.1
        reading.confirm(memberId, clock.instant());                           // 2.2
        measurementStore.save(reading);                                       // 2.3
        return reading;
    }

    public WeightReading rejectReading(String readingId) {
        WeightReading reading = load(readingId);
        reading.reject();
        measurementStore.save(reading);
        return reading;
    }

    private WeightReading load(String readingId) {
        return measurementStore.findById(readingId)
                .orElseThrow(() -> new IllegalArgumentException("Unknown reading " + readingId));
    }
}
