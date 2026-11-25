package com.gymarena.challenge;

import java.time.Duration;
import java.time.Instant;
import java.util.Objects;

/**
 * One versioned challenge rule for an exercise and level (FR-14.1). State diagram:
 * DRAFT -> APPROVED -> SUPERSEDED, or DRAFT -> REJECTED.
 */
public class ChallengeRuleVersion {

    private final String ruleId;
    private final String exercise;
    private final int level;
    private final int version;
    private final int targetRepetitions;
    private final Duration timeAllowance;
    private final int completionPoints;
    private final int timeoutDeduction;
    private final WinnerRule winnerRule;
    private RuleStatus status = RuleStatus.DRAFT;
    private String approvedBy;
    private Instant approvedAt;
    private String rejectionReason;
    private Instant supersededAt;

    /** [*] --create [target > 0, time > 0, points >= 0] --> DRAFT. */
    public ChallengeRuleVersion(String ruleId, String exercise, int level, int version, int targetRepetitions,
                                Duration timeAllowance, int completionPoints, int timeoutDeduction,
                                WinnerRule winnerRule) {
        this.ruleId = requireText(ruleId, "ruleId");
        this.exercise = requireText(exercise, "exercise");
        if (level < 1 || version < 1) {
            throw new IllegalArgumentException("level and version start at 1");
        }
        if (targetRepetitions <= 0) {
            throw new IllegalArgumentException("targetRepetitions must be positive");
        }
        Objects.requireNonNull(timeAllowance, "timeAllowance");
        if (timeAllowance.isZero() || timeAllowance.isNegative()) {
            throw new IllegalArgumentException("timeAllowance must be positive");
        }
        if (completionPoints < 0 || timeoutDeduction < 0) {
            throw new IllegalArgumentException("points and deduction are non-negative magnitudes");
        }
        this.level = level;
        this.version = version;
        this.targetRepetitions = targetRepetitions;
        this.timeAllowance = timeAllowance;
        this.completionPoints = completionPoints;
        this.timeoutDeduction = timeoutDeduction;
        this.winnerRule = Objects.requireNonNull(winnerRule, "winnerRule");
    }

    /** Restores an already approved version (repository and test fixtures). */
    public static ChallengeRuleVersion approved(ChallengeRuleVersion draft, String trainerId, Instant at) {
        draft.approve(trainerId, at);
        return draft;
    }

    /** DRAFT --approve(trainerId) [trainer given] / approvedBy, approvedAt --> APPROVED (FR-14.1, FR-13.3). */
    public void approve(String trainerId, Instant now) {
        requireStatus(RuleStatus.DRAFT, "approve");
        this.approvedBy = requireText(trainerId, "trainerId");
        this.approvedAt = Objects.requireNonNull(now, "now");
        this.status = RuleStatus.APPROVED;
    }

    /** DRAFT --reject(trainerId, reason) [reason given] --> REJECTED. */
    public void reject(String trainerId, String reason) {
        requireStatus(RuleStatus.DRAFT, "reject");
        requireText(trainerId, "trainerId");
        this.rejectionReason = requireText(reason, "reason");
        this.status = RuleStatus.REJECTED;
    }

    /** APPROVED --supersede() [a newer version was approved] --> SUPERSEDED. */
    public void supersede(Instant now) {
        requireStatus(RuleStatus.APPROVED, "supersede");
        this.supersededAt = Objects.requireNonNull(now, "now");
        this.status = RuleStatus.SUPERSEDED;
    }

    /** FR-14.5: only an approved version can be shown before an attempt. */
    public RuleSummary summary() {
        requireStatus(RuleStatus.APPROVED, "present");
        return new RuleSummary(exercise, level, version, targetRepetitions, timeAllowance, completionPoints,
                timeoutDeduction, winnerRule);
    }

    private void requireStatus(RuleStatus required, String operation) {
        if (status != required) {
            throw new IllegalStateException("Cannot " + operation + " a rule in state " + status);
        }
    }

    private static String requireText(String value, String name) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(name + " is required");
        }
        return value;
    }

    public String getRuleId() { return ruleId; }
    public String getExercise() { return exercise; }
    public int getLevel() { return level; }
    public int getVersion() { return version; }
    public int getTargetRepetitions() { return targetRepetitions; }
    public Duration getTimeAllowance() { return timeAllowance; }
    public int getCompletionPoints() { return completionPoints; }
    public int getTimeoutDeduction() { return timeoutDeduction; }
    public WinnerRule getWinnerRule() { return winnerRule; }
    public RuleStatus getStatus() { return status; }
    public String getApprovedBy() { return approvedBy; }
    public Instant getApprovedAt() { return approvedAt; }
    public String getRejectionReason() { return rejectionReason; }
    public Instant getSupersededAt() { return supersededAt; }
}
