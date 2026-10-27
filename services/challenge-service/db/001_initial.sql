-- GymArena challenge-service draft schema
-- Target database: gymarena_challenge. Run this file only in this service database.
-- REF fields describe remote IDs and intentionally have no cross-database FK.
-- Application-generated UUIDs; no extension or UUID default is required.
BEGIN;

CREATE TABLE "assessments" (
  "assessment_id" UUID NOT NULL,
  "member_id" UUID NOT NULL,
  "exercise" TEXT NOT NULL,
  "observed_repetitions" INTEGER NOT NULL,
  "active_ms" BIGINT NOT NULL,
  "trainer_id" UUID NOT NULL,
  "observed_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("assessment_id"),
  UNIQUE ("assessment_id", "member_id", "exercise"),
  CHECK (exercise IN ('SQUAT', 'JUMPING_JACK')),
  CHECK (observed_repetitions >= 0),
  CHECK (active_ms > 0)
);

COMMENT ON COLUMN "assessments"."member_id" IS 'External identity reference: member-service.members.member_id; resolve through the owning service API, never by direct database access.';

COMMENT ON COLUMN "assessments"."trainer_id" IS 'External identity reference: authenticated trainer principal; resolve through the owning service API, never by direct database access.';

CREATE TABLE "level_approvals" (
  "approval_id" UUID NOT NULL,
  "assessment_id" UUID NOT NULL,
  "member_id" UUID NOT NULL,
  "exercise" TEXT NOT NULL,
  "approved_level" INTEGER NOT NULL,
  "trainer_id" UUID NOT NULL,
  "approved_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("approval_id"),
  UNIQUE ("assessment_id"),
  UNIQUE ("approval_id", "member_id", "exercise"),
  CHECK (approved_level > 0),
  FOREIGN KEY ("assessment_id", "member_id", "exercise") REFERENCES "assessments" ("assessment_id", "member_id", "exercise") ON DELETE RESTRICT
);

COMMENT ON COLUMN "level_approvals"."member_id" IS 'External identity reference: member-service.members.member_id; resolve through the owning service API, never by direct database access.';

COMMENT ON COLUMN "level_approvals"."trainer_id" IS 'External identity reference: authenticated trainer principal; resolve through the owning service API, never by direct database access.';

CREATE TABLE "current_levels" (
  "member_id" UUID NOT NULL,
  "exercise" TEXT NOT NULL,
  "approval_id" UUID NOT NULL,
  PRIMARY KEY ("member_id", "exercise"),
  UNIQUE ("approval_id"),
  FOREIGN KEY ("approval_id", "member_id", "exercise") REFERENCES "level_approvals" ("approval_id", "member_id", "exercise") ON DELETE RESTRICT
);

COMMENT ON COLUMN "current_levels"."member_id" IS 'External identity reference: member-service.members.member_id; resolve through the owning service API, never by direct database access.';

CREATE TABLE "challenge_rule_versions" (
  "rule_version_id" UUID NOT NULL,
  "exercise" TEXT NOT NULL,
  "level" INTEGER NOT NULL,
  "target_repetitions" INTEGER NOT NULL,
  "active_limit_ms" BIGINT NOT NULL,
  "reward_points" INTEGER NOT NULL,
  "timeout_deduction" INTEGER NOT NULL,
  "winner_rule" TEXT NOT NULL,
  "approved_by" UUID,
  "approved_at" TIMESTAMPTZ,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("rule_version_id"),
  UNIQUE ("rule_version_id", "exercise"),
  CHECK (exercise IN ('SQUAT', 'JUMPING_JACK')),
  CHECK (level > 0),
  CHECK (target_repetitions > 0),
  CHECK (active_limit_ms > 0),
  CHECK (reward_points >= 0),
  CHECK (timeout_deduction >= 0),
  CHECK ((approved_by IS NULL) = (approved_at IS NULL))
);

COMMENT ON COLUMN "challenge_rule_versions"."approved_by" IS 'External identity reference: authenticated trainer principal; resolve through the owning service API, never by direct database access.';

CREATE TABLE "challenge_assignments" (
  "assignment_id" UUID NOT NULL,
  "member_id" UUID NOT NULL,
  "exercise" TEXT NOT NULL,
  "rule_version_id" UUID NOT NULL,
  "basis_approval_id" UUID NOT NULL,
  "assigned_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("assignment_id"),
  FOREIGN KEY ("rule_version_id", "exercise") REFERENCES "challenge_rule_versions" ("rule_version_id", "exercise") ON DELETE RESTRICT,
  FOREIGN KEY ("basis_approval_id", "member_id", "exercise") REFERENCES "level_approvals" ("approval_id", "member_id", "exercise") ON DELETE RESTRICT
);

COMMENT ON COLUMN "challenge_assignments"."member_id" IS 'External identity reference: member-service.members.member_id; resolve through the owning service API, never by direct database access.';

CREATE INDEX "assessment_member_exercise_time" ON "assessments" ("member_id", "exercise", "observed_at");

COMMIT;
