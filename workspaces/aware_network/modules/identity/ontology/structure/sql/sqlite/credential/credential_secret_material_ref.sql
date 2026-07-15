-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE credential_secret_material_ref (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  credential_profile_id TEXT NOT NULL,
  -- ATTRIBUTES
  secret_ref_key TEXT NOT NULL,
  resolver_kind TEXT NOT NULL,
  secret_name TEXT NOT NULL,
  locator TEXT,
  username_hint TEXT,
  material_hint TEXT,
  fingerprint_sha256 TEXT,
  created_at_utc TEXT,
  rotated_at_utc TEXT,
  metadata TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, credential_profile_id, secret_ref_key, resolver_kind),
  FOREIGN KEY (branch_id, projection_hash, credential_profile_id) REFERENCES credential_profile(branch_id, projection_hash, id)
);
