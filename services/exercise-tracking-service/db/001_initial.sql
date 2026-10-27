-- GymArena exercise-tracking-service draft schema
-- Target database: gymarena_tracking. Run this file only in this service database.
-- REF fields describe remote IDs and intentionally have no cross-database FK.
-- Application-generated UUIDs; no extension or UUID default is required.
BEGIN;

CREATE TABLE "exercise_configs" (
  "config_id" UUID NOT NULL,
  "exercise" TEXT NOT NULL,
  "version" INTEGER NOT NULL,
  "min_visibility" NUMERIC(4,3) NOT NULL,
  "min_cycle_ms" INTEGER NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("config_id"),
  UNIQUE ("exercise", "version"),
  CHECK (exercise IN ('SQUAT', 'JUMPING_JACK')),
  CHECK (version > 0),
  CHECK (min_visibility BETWEEN 0 AND 1),
  CHECK (min_cycle_ms >= 0)
);

CREATE TABLE "phase_rules" (
  "phase_rule_id" UUID NOT NULL,
  "config_id" UUID NOT NULL,
  "phase" SMALLINT NOT NULL,
  "feature_name" TEXT NOT NULL,
  "comparison" TEXT NOT NULL,
  "threshold" NUMERIC(9,3) NOT NULL,
  PRIMARY KEY ("phase_rule_id"),
  UNIQUE ("config_id", "phase", "feature_name"),
  CHECK (phase IN (0,1)),
  CHECK (comparison IN ('LE', 'GE')),
  FOREIGN KEY ("config_id") REFERENCES "exercise_configs" ("config_id") ON DELETE RESTRICT
);

CREATE TABLE "tracking_diagnostics" (
  "diagnostic_id" UUID NOT NULL,
  "session_id" UUID NOT NULL,
  "member_id" UUID,
  "config_id" UUID,
  "reason_code" TEXT NOT NULL,
  "position" SMALLINT,
  "observed_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("diagnostic_id"),
  CHECK (position IS NULL OR position IN (1,2)),
  FOREIGN KEY ("config_id") REFERENCES "exercise_configs" ("config_id") ON DELETE RESTRICT
);

COMMENT ON COLUMN "tracking_diagnostics"."session_id" IS 'External identity reference: session-service.sessions.session_id; resolve through the owning service API, never by direct database access.';

COMMENT ON COLUMN "tracking_diagnostics"."member_id" IS 'External identity reference: member-service.members.member_id; resolve through the owning service API, never by direct database access.';

CREATE INDEX "tracking_diagnostics_session_time" ON "tracking_diagnostics" ("session_id", "observed_at");

COMMIT;
