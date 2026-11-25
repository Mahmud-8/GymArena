package com.gymarena.member;

/** Narrow port to IScaleInput; realized by SerialScaleAdapter. */
public interface IScaleSource {
    ScaleReading readStableWeight();
}
