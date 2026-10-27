-- GymArena recognition-service draft schema
-- Target database: gymarena_recognition. Run this file only in this service database.
-- REF fields describe remote IDs and intentionally have no cross-database FK.
-- Application-generated UUIDs; no extension or UUID default is required.
BEGIN;

CREATE TABLE "face_enrollments" (
  "member_id" UUID NOT NULL,
  "agreed_at" TIMESTAMPTZ NOT NULL,
  "withdrawn_at" TIMESTAMPTZ,
  "version" INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY ("member_id"),
  CHECK (withdrawn_at IS NULL OR withdrawn_at >= agreed_at),
  CHECK (version > 0)
);

COMMENT ON COLUMN "face_enrollments"."member_id" IS 'External identity reference: member-service.members.member_id; resolve through the owning service API, never by direct database access.';

CREATE TABLE "face_references" (
  "reference_id" UUID NOT NULL,
  "member_id" UUID NOT NULL,
  "encrypted_embedding" BYTEA NOT NULL,
  "model_tag" TEXT NOT NULL,
  "quality_score" NUMERIC(4,3) NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("reference_id"),
  UNIQUE ("member_id"),
  CHECK (quality_score BETWEEN 0 AND 1),
  FOREIGN KEY ("member_id") REFERENCES "face_enrollments" ("member_id") ON DELETE RESTRICT
);

CREATE TABLE "identity_contexts" (
  "context_id" UUID NOT NULL,
  "member_id" UUID NOT NULL,
  "source" TEXT NOT NULL,
  "token_digest" TEXT NOT NULL,
  "reference_id" UUID,
  "confirmed_at" TIMESTAMPTZ NOT NULL,
  "expires_at" TIMESTAMPTZ NOT NULL,
  "revoked_at" TIMESTAMPTZ,
  "confirmed_by_staff" UUID,
  PRIMARY KEY ("context_id"),
  UNIQUE ("token_digest"),
  CHECK (source IN ('FACE', 'MEMBER_CODE', 'STAFF')),
  CHECK (expires_at > confirmed_at),
  CHECK (revoked_at IS NULL OR revoked_at >= confirmed_at),
  FOREIGN KEY ("reference_id") REFERENCES "face_references" ("reference_id") ON DELETE SET NULL
);

COMMENT ON COLUMN "identity_contexts"."member_id" IS 'External identity reference: member-service.members.member_id; resolve through the owning service API, never by direct database access.';

COMMENT ON COLUMN "identity_contexts"."confirmed_by_staff" IS 'External identity reference: authenticated staff principal; resolve through the owning service API, never by direct database access.';

CREATE INDEX "identity_context_member_expiry" ON "identity_contexts" ("member_id", "expires_at");

COMMIT;
