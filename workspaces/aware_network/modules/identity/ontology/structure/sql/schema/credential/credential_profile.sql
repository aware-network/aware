-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE credential_profile (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  identity_id UUID NOT NULL,
  -- ATTRIBUTES
  profile_key TEXT NOT NULL,
  target_kind credential_target_kind NOT NULL,
  credential_kind credential_kind NOT NULL,
  status credential_profile_status NOT NULL,
  display_name TEXT,
  target_name TEXT,
  issuer TEXT,
  audience TEXT,
  external_subject TEXT,
  created_at_utc TEXT,
  updated_at_utc TEXT,
  expires_at_utc TEXT,
  revoked_at_utc TEXT,
  metadata JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, identity_id, profile_key, target_kind)
);
