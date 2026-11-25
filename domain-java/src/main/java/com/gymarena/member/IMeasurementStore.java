package com.gymarena.member;

import java.util.Optional;

/** Measurement persistence port; realized by SqlMemberStore (weight_measurements). */
public interface IMeasurementStore {
    String nextReadingId();

    Optional<WeightReading> findById(String readingId);

    void save(WeightReading reading);
}
