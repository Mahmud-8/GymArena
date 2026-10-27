-- GymArena member-service draft schema
-- Target database: gymarena_member. Run this file only in this service database.
-- REF fields describe remote IDs and intentionally have no cross-database FK.
-- Application-generated UUIDs; no extension or UUID default is required.
BEGIN;

CREATE TABLE "members" (
  "member_id" UUID NOT NULL,
  "full_name" TEXT NOT NULL,
  "age" SMALLINT NOT NULL,
  "member_code" TEXT NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("member_id"),
  UNIQUE ("member_code"),
  CHECK (length(btrim(full_name)) > 0),
  CHECK (age > 0),
  CHECK (length(btrim(member_code)) > 0)
);

CREATE TABLE "weight_measurements" (
  "measurement_id" UUID NOT NULL,
  "member_id" UUID NOT NULL,
  "weight_kg" NUMERIC(7,3) NOT NULL,
  "captured_at" TIMESTAMPTZ NOT NULL,
  "confirmed_at" TIMESTAMPTZ NOT NULL,
  PRIMARY KEY ("measurement_id"),
  CHECK (weight_kg > 0),
  CHECK (confirmed_at >= captured_at),
  FOREIGN KEY ("member_id") REFERENCES "members" ("member_id") ON DELETE RESTRICT
);

CREATE TABLE "member_registered_outbox" (
  "event_id" UUID NOT NULL,
  "feed_sequence" BIGINT NOT NULL,
  "member_id" UUID NOT NULL,
  "display_name" TEXT NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("event_id"),
  UNIQUE ("feed_sequence"),
  UNIQUE ("member_id"),
  CHECK (feed_sequence > 0),
  FOREIGN KEY ("member_id") REFERENCES "members" ("member_id") ON DELETE RESTRICT
);

CREATE TABLE "registration_feed_state" (
  "feed_name" TEXT NOT NULL,
  "last_sequence" BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("feed_name"),
  CHECK (feed_name = 'registrations'),
  CHECK (last_sequence >= 0)
);

INSERT INTO registration_feed_state(feed_name, last_sequence) VALUES ('registrations', 0);
CREATE INDEX "member_weight_history" ON "weight_measurements" ("member_id", "captured_at");

COMMIT;
