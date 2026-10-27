-- GymArena membership-service draft schema
-- Target database: gymarena_membership. Run this file only in this service database.
-- REF fields describe remote IDs and intentionally have no cross-database FK.
-- Application-generated UUIDs; no extension or UUID default is required.
BEGIN;

CREATE TABLE "memberships" (
  "member_id" UUID NOT NULL,
  "start_date" DATE NOT NULL,
  "expiry_date" DATE NOT NULL,
  "whatsapp_number" TEXT NOT NULL,
  "version" INTEGER NOT NULL DEFAULT 1,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("member_id"),
  CHECK (expiry_date >= start_date),
  CHECK (length(btrim(whatsapp_number)) > 0),
  CHECK (version > 0)
);

COMMENT ON COLUMN "memberships"."member_id" IS 'External identity reference: member-service.members.member_id; resolve through the owning service API, never by direct database access.';

CREATE TABLE "renewal_records" (
  "renewal_id" UUID NOT NULL,
  "member_id" UUID NOT NULL,
  "previous_expiry" DATE NOT NULL,
  "revised_expiry" DATE NOT NULL,
  "recorded_by" UUID NOT NULL,
  "recorded_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("renewal_id"),
  CHECK (revised_expiry > previous_expiry),
  FOREIGN KEY ("member_id") REFERENCES "memberships" ("member_id") ON DELETE RESTRICT
);

COMMENT ON COLUMN "renewal_records"."recorded_by" IS 'External identity reference: authenticated staff principal; resolve through the owning service API, never by direct database access.';

CREATE TABLE "renewal_outbox" (
  "event_id" UUID NOT NULL,
  "feed_sequence" BIGINT NOT NULL,
  "renewal_id" UUID NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("event_id"),
  UNIQUE ("feed_sequence"),
  UNIQUE ("renewal_id"),
  CHECK (feed_sequence > 0),
  FOREIGN KEY ("renewal_id") REFERENCES "renewal_records" ("renewal_id") ON DELETE RESTRICT
);

CREATE TABLE "renewal_feed_state" (
  "feed_name" TEXT NOT NULL,
  "last_sequence" BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("feed_name"),
  CHECK (feed_name = 'renewals'),
  CHECK (last_sequence >= 0)
);

INSERT INTO renewal_feed_state(feed_name, last_sequence) VALUES ('renewals', 0);
CREATE INDEX "membership_expiry" ON "memberships" ("expiry_date");

COMMIT;
