-- GymArena scoring-service draft schema
-- Target database: gymarena_scoring. Run this file only in this service database.
-- REF fields describe remote IDs and intentionally have no cross-database FK.
-- Application-generated UUIDs; no extension or UUID default is required.
BEGIN;

CREATE TABLE "member_scores" (
  "member_id" UUID NOT NULL,
  "display_name" TEXT NOT NULL,
  "points_balance" BIGINT NOT NULL DEFAULT 0,
  "leaderboard_points" BIGINT NOT NULL DEFAULT 0,
  "registration_event_id" UUID,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("member_id"),
  UNIQUE ("registration_event_id")
);

COMMENT ON COLUMN "member_scores"."member_id" IS 'External identity reference: member-service.members.member_id; resolve through the owning service API, never by direct database access.';

COMMENT ON COLUMN "member_scores"."registration_event_id" IS 'External identity reference: member-service.member_registered_outbox.event_id; resolve through the owning service API, never by direct database access.';

CREATE TABLE "processed_sessions" (
  "session_id" UUID NOT NULL,
  "outcome_fingerprint" TEXT NOT NULL,
  "outcome_status" TEXT NOT NULL,
  "ranked" BOOLEAN NOT NULL,
  "winner_member_id" UUID,
  "is_tie" BOOLEAN NOT NULL DEFAULT FALSE,
  "processed_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("session_id"),
  CHECK (outcome_status IN ('VALID_COMPLETED', 'INCOMPLETE', 'STOPPED')),
  CHECK (outcome_status = 'VALID_COMPLETED' OR (winner_member_id IS NULL AND is_tie = FALSE)),
  CHECK (winner_member_id IS NULL OR is_tie = FALSE),
  FOREIGN KEY ("winner_member_id") REFERENCES "member_scores" ("member_id") ON DELETE RESTRICT
);

COMMENT ON COLUMN "processed_sessions"."session_id" IS 'External identity reference: session-service.session_outcomes.session_id; resolve through the owning service API, never by direct database access.';

CREATE TABLE "score_entries" (
  "entry_id" UUID NOT NULL,
  "session_id" UUID NOT NULL,
  "member_id" UUID NOT NULL,
  "delta" INTEGER NOT NULL,
  "reason" TEXT NOT NULL,
  "leaderboard_eligible" BOOLEAN NOT NULL,
  "rule_version_id" UUID NOT NULL,
  "exercise" TEXT NOT NULL,
  "challenge_level" INTEGER NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("entry_id"),
  UNIQUE ("session_id", "member_id"),
  CHECK (exercise IN ('SQUAT', 'JUMPING_JACK')),
  CHECK (challenge_level > 0),
  FOREIGN KEY ("session_id") REFERENCES "processed_sessions" ("session_id") ON DELETE RESTRICT,
  FOREIGN KEY ("member_id") REFERENCES "member_scores" ("member_id") ON DELETE RESTRICT
);

COMMENT ON COLUMN "score_entries"."rule_version_id" IS 'External identity reference: challenge-service.challenge_rule_versions.rule_version_id; resolve through the owning service API, never by direct database access.';

CREATE TABLE "leaderboard_state" (
  "state_id" SMALLINT NOT NULL,
  "version" BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("state_id"),
  CHECK (state_id = 1),
  CHECK (version >= 0)
);

CREATE TABLE "leaderboard_outbox" (
  "event_id" UUID NOT NULL,
  "version" BIGINT NOT NULL,
  "event_type" TEXT NOT NULL,
  "session_id" UUID,
  "committed_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("event_id"),
  UNIQUE ("version"),
  UNIQUE ("session_id"),
  CHECK (version > 0),
  CHECK (event_type IN ('MEMBER_REGISTERED', 'POINTS_UPDATED')),
  CHECK ((event_type = 'MEMBER_REGISTERED' AND session_id IS NULL) OR (event_type = 'POINTS_UPDATED' AND session_id IS NOT NULL)),
  FOREIGN KEY ("session_id") REFERENCES "processed_sessions" ("session_id") ON DELETE RESTRICT
);

CREATE TABLE "leaderboard_outbox_members" (
  "event_id" UUID NOT NULL,
  "member_id" UUID NOT NULL,
  PRIMARY KEY ("event_id", "member_id"),
  FOREIGN KEY ("event_id") REFERENCES "leaderboard_outbox" ("event_id") ON DELETE RESTRICT,
  FOREIGN KEY ("member_id") REFERENCES "member_scores" ("member_id") ON DELETE RESTRICT
);

CREATE TABLE "registration_cursors" (
  "consumer_name" TEXT NOT NULL,
  "last_sequence" BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("consumer_name"),
  CHECK (consumer_name = 'member-registration'),
  CHECK (last_sequence >= 0)
);

INSERT INTO leaderboard_state(state_id, version) VALUES (1, 0);
INSERT INTO registration_cursors(consumer_name, last_sequence) VALUES ('member-registration', 0);
CREATE INDEX "member_score_history" ON "score_entries" ("member_id", "created_at");
CREATE INDEX "comparable_score_scope" ON "score_entries" ("exercise", "challenge_level", "leaderboard_eligible");

CREATE VIEW overall_leaderboard AS
SELECT member_id, display_name, leaderboard_points,
       RANK() OVER (ORDER BY leaderboard_points DESC) AS position
FROM member_scores;

CREATE VIEW comparable_leaderboard AS
WITH totals AS (
  SELECT member_id, exercise, challenge_level, SUM(delta) AS points
  FROM score_entries WHERE leaderboard_eligible = TRUE
  GROUP BY member_id, exercise, challenge_level
)
SELECT member_id, exercise, challenge_level, points,
       RANK() OVER (
         PARTITION BY exercise, challenge_level ORDER BY points DESC
       ) AS position
FROM totals;

COMMIT;
