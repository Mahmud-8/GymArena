-- GymArena notification-service draft schema
-- Target database: gymarena_notification. Run this file only in this service database.
-- REF fields describe remote IDs and intentionally have no cross-database FK.
-- Application-generated UUIDs; no extension or UUID default is required.
BEGIN;

CREATE TABLE "reminder_settings" (
  "settings_id" SMALLINT NOT NULL,
  "gym_timezone" TEXT NOT NULL,
  "send_time" TIME NOT NULL,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("settings_id"),
  CHECK (settings_id = 1),
  CHECK (length(btrim(gym_timezone)) > 0)
);

CREATE TABLE "reminder_offsets" (
  "offset_id" UUID NOT NULL,
  "settings_id" SMALLINT NOT NULL,
  "offset_days" INTEGER NOT NULL,
  "enabled" BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY ("offset_id"),
  UNIQUE ("settings_id", "offset_days"),
  FOREIGN KEY ("settings_id") REFERENCES "reminder_settings" ("settings_id") ON DELETE RESTRICT
);

CREATE TABLE "reminder_jobs" (
  "job_id" UUID NOT NULL,
  "member_id" UUID NOT NULL,
  "offset_id" UUID NOT NULL,
  "expected_expiry" DATE NOT NULL,
  "offset_days" INTEGER NOT NULL,
  "channel" TEXT NOT NULL DEFAULT 'WHATSAPP',
  "due_at" TIMESTAMPTZ NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'PENDING',
  "lease_until" TIMESTAMPTZ,
  "released_at" TIMESTAMPTZ,
  "version" INTEGER NOT NULL DEFAULT 1,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("job_id"),
  UNIQUE ("member_id", "expected_expiry", "offset_days", "channel"),
  CHECK (channel = 'WHATSAPP'),
  CHECK (status IN ('PENDING', 'CLAIMED', 'RELEASED', 'CANCELLED', 'ACCEPTED', 'FAILED')),
  CHECK (version > 0),
  FOREIGN KEY ("offset_id") REFERENCES "reminder_offsets" ("offset_id") ON DELETE RESTRICT
);

COMMENT ON COLUMN "reminder_jobs"."member_id" IS 'External identity reference: member-service.members.member_id; resolve through the owning service API, never by direct database access.';

CREATE TABLE "message_records" (
  "message_id" UUID NOT NULL,
  "job_id" UUID,
  "member_id" UUID NOT NULL,
  "kind" TEXT NOT NULL,
  "recipient" TEXT NOT NULL,
  "dedupe_key" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "selection_reason" TEXT NOT NULL,
  "provider_message_id" TEXT,
  "status" TEXT NOT NULL DEFAULT 'PENDING',
  "submission_uncertain" BOOLEAN NOT NULL DEFAULT FALSE,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("message_id"),
  UNIQUE ("job_id"),
  UNIQUE ("dedupe_key"),
  UNIQUE ("provider_message_id"),
  CHECK (kind IN ('RENEWAL', 'ACTIVITY', 'INVITATION')),
  CHECK (status IN ('PENDING', 'ACCEPTED', 'DELIVERED', 'FAILED')),
  CHECK (length(btrim(recipient)) > 0),
  FOREIGN KEY ("job_id") REFERENCES "reminder_jobs" ("job_id") ON DELETE RESTRICT
);

COMMENT ON COLUMN "message_records"."member_id" IS 'External identity reference: member-service.members.member_id; resolve through the owning service API, never by direct database access.';

CREATE TABLE "delivery_attempts" (
  "attempt_id" UUID NOT NULL,
  "message_id" UUID NOT NULL,
  "attempt_number" INTEGER NOT NULL,
  "outcome" TEXT NOT NULL,
  "provider_message_id" TEXT,
  "error_code" TEXT,
  "attempted_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("attempt_id"),
  UNIQUE ("message_id", "attempt_number"),
  CHECK (attempt_number > 0),
  CHECK (outcome IN ('ACCEPTED', 'FAILED', 'UNCERTAIN')),
  FOREIGN KEY ("message_id") REFERENCES "message_records" ("message_id") ON DELETE RESTRICT
);

CREATE TABLE "message_status_events" (
  "status_event_id" UUID NOT NULL,
  "message_id" UUID NOT NULL,
  "provider_event_id" TEXT,
  "status" TEXT NOT NULL,
  "provider_occurred_at" TIMESTAMPTZ,
  "received_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("status_event_id"),
  UNIQUE ("provider_event_id"),
  CHECK (status IN ('ACCEPTED', 'DELIVERED', 'FAILED')),
  FOREIGN KEY ("message_id") REFERENCES "message_records" ("message_id") ON DELETE RESTRICT
);

CREATE TABLE "renewal_cursors" (
  "consumer_name" TEXT NOT NULL,
  "last_sequence" BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("consumer_name"),
  CHECK (consumer_name = 'membership-renewals'),
  CHECK (last_sequence >= 0)
);

INSERT INTO renewal_cursors(consumer_name, last_sequence) VALUES ('membership-renewals', 0);
CREATE INDEX "due_reminder_jobs" ON "reminder_jobs" ("status", "due_at");
CREATE INDEX "member_message_history" ON "message_records" ("member_id", "created_at");

COMMIT;
