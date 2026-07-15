-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE credential_profile (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  identity_id TEXT NOT NULL,
  -- ATTRIBUTES
  profile_key TEXT NOT NULL,
  target_kind TEXT NOT NULL,
  credential_kind TEXT NOT NULL,
  status TEXT NOT NULL,
  display_name TEXT,
  target_name TEXT,
  issuer TEXT,
  audience TEXT,
  external_subject TEXT,
  created_at_utc TEXT,
  updated_at_utc TEXT,
  expires_at_utc TEXT,
  revoked_at_utc TEXT,
  metadata TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, identity_id, profile_key, target_kind)
);
