-- Additive migration for both existing and new member databases.
-- Keeps retry intent separate from the member profile and immutable event.
CREATE TABLE IF NOT EXISTS member_registration_requests (
  request_id UUID PRIMARY KEY,
  payload_hash TEXT NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
  member_id UUID NOT NULL UNIQUE REFERENCES members(member_id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
