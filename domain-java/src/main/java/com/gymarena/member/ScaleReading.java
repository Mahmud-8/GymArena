package com.gymarena.member;

import java.time.Instant;

/** Raw value supplied by the electronic scale through IScaleSource (FR-10.1). */
public record ScaleReading(double weightKg, boolean stable, Instant readAt) {

    public static final double MIN_KG = 20.0;
    public static final double MAX_KG = 300.0;

    /** FR-10.4: only a stable reading inside the supported range is valid. */
    public boolean isValid() {
        return stable && weightKg >= MIN_KG && weightKg <= MAX_KG;
    }
}
