package com.gymarena.challenge;

import java.time.Duration;

/** Rules shown to the member before an attempt starts (FR-14.5). */
public record RuleSummary(String exercise, int level, int version, int targetRepetitions, Duration timeAllowance,
                          int completionPoints, int timeoutDeduction, WinnerRule winnerRule) {
}
