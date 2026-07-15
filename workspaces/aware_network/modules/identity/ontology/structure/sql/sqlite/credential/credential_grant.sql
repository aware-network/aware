-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE credential_grant (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  credential_profile_id TEXT NOT NULL,
  -- ATTRIBUTES
  grant_key TEXT NOT NULL,
  effect TEXT NOT NULL,
  scope_kind TEXT NOT NULL,
  scope_value TEXT NOT NULL,
  operation TEXT,
  resource_ref TEXT,
  expires_at_utc TEXT,
  metadata TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, credential_profile_id, grant_key, scope_kind, scope_value),
  FOREIGN KEY (branch_id, projection_hash, credential_profile_id) REFERENCES credential_profile(branch_id, projection_hash, id)
);
