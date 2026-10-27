-- GymArena session-service draft schema
-- Target database: gymarena_session. Run this file only in this service database.
-- REF fields describe remote IDs and intentionally have no cross-database FK.
-- Application-generated UUIDs; no extension or UUID default is required.
BEGIN;

CREATE TABLE "sessions" (
  "session_id" UUID NOT NULL,
  "mode" TEXT NOT NULL,
  "ranked" BOOLEAN NOT NULL,
  "exercise" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "active_limit_ms" BIGINT NOT NULL,
  "active_elapsed_ms" BIGINT NOT NULL DEFAULT 0,
  "active_started_at" TIMESTAMPTZ,
  "winner_rule" TEXT NOT NULL,
  "version" INTEGER NOT NULL DEFAULT 1,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "ended_at" TIMESTAMPTZ,
  PRIMARY KEY ("session_id"),
  CHECK (mode IN ('SOLO', 'LOCAL_1V1')),
  CHECK (exercise IN ('SQUAT', 'JUMPING_JACK')),
  CHECK (status IN ('CREATED', 'ACTIVE', 'PAUSED', 'VALID_COMPLETED', 'INCOMPLETE', 'STOPPED')),
  CHECK (active_limit_ms > 0),
  CHECK (active_elapsed_ms >= 0),
  CHECK (version > 0)
);

CREATE TABLE "session_participants" (
  "session_id" UUID NOT NULL,
  "member_id" UUID NOT NULL,
  "position" SMALLINT NOT NULL,
  "accepted_count" INTEGER NOT NULL DEFAULT 0,
  "target_completed" BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY ("session_id", "member_id"),
  UNIQUE ("session_id", "position"),
  CHECK (position IN (1,2)),
  CHECK (accepted_count >= 0),
  FOREIGN KEY ("session_id") REFERENCES "sessions" ("session_id") ON DELETE RESTRICT
);

COMMENT ON COLUMN "session_participants"."member_id" IS 'External identity reference: member-service.members.member_id; resolve through the owning service API, never by direct database access.';

CREATE TABLE "participant_rule_snapshots" (
  "session_id" UUID NOT NULL,
  "member_id" UUID NOT NULL,
  "source_assignment_id" UUID NOT NULL,
  "source_rule_version" UUID NOT NULL,
  "challenge_level" INTEGER NOT NULL,
  "target_repetitions" INTEGER NOT NULL,
  "reward_points" INTEGER NOT NULL,
  "timeout_deduction" INTEGER NOT NULL,
  PRIMARY KEY ("session_id", "member_id"),
  CHECK (challenge_level > 0),
  CHECK (target_repetitions > 0),
  CHECK (reward_points >= 0),
  CHECK (timeout_deduction >= 0),
  FOREIGN KEY ("session_id", "member_id") REFERENCES "session_participants" ("session_id", "member_id") ON DELETE RESTRICT
);

COMMENT ON COLUMN "participant_rule_snapshots"."source_assignment_id" IS 'External identity reference: challenge-service.challenge_assignments.assignment_id; resolve through the owning service API, never by direct database access.';

COMMENT ON COLUMN "participant_rule_snapshots"."source_rule_version" IS 'External identity reference: challenge-service.challenge_rule_versions.rule_version_id; resolve through the owning service API, never by direct database access.';

CREATE TABLE "session_interruptions" (
  "interruption_id" UUID NOT NULL,
  "session_id" UUID NOT NULL,
  "affected_member_id" UUID,
  "reason" TEXT NOT NULL,
  "started_at" TIMESTAMPTZ NOT NULL,
  "resolved_at" TIMESTAMPTZ,
  PRIMARY KEY ("interruption_id"),
  CHECK (resolved_at IS NULL OR resolved_at >= started_at),
  FOREIGN KEY ("session_id") REFERENCES "sessions" ("session_id") ON DELETE RESTRICT,
  FOREIGN KEY ("session_id", "affected_member_id") REFERENCES "session_participants" ("session_id", "member_id") ON DELETE RESTRICT
);

CREATE TABLE "session_outcomes" (
  "session_id" UUID NOT NULL,
  "final_status" TEXT NOT NULL,
  "outcome_version" INTEGER NOT NULL,
  "outcome_fingerprint" TEXT NOT NULL,
  "active_elapsed_ms" BIGINT NOT NULL,
  "finalized_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("session_id"),
  CHECK (final_status IN ('VALID_COMPLETED', 'INCOMPLETE', 'STOPPED')),
  CHECK (outcome_version > 0),
  CHECK (active_elapsed_ms >= 0),
  FOREIGN KEY ("session_id") REFERENCES "sessions" ("session_id") ON DELETE RESTRICT
);

CREATE INDEX "session_member_history" ON "session_participants" ("member_id", "session_id");

COMMIT;
