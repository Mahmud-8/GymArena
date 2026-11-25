package com.gymarena.member;

/** FR-10.4: reported to the kiosk; the last accepted measurement is kept. */
public class InvalidScaleReadingException extends RuntimeException {
    public InvalidScaleReadingException(ScaleReading reading) {
        super("Invalid scale reading: " + reading.weightKg() + " kg, stable=" + reading.stable());
    }
}
