-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE credential_secret_material_ref (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  credential_profile_id UUID NOT NULL,
  -- ATTRIBUTES
  secret_ref_key TEXT NOT NULL,
  resolver_kind credential_secret_resolver_kind NOT NULL,
  secret_name TEXT NOT NULL,
  locator TEXT,
  username_hint TEXT,
  material_hint TEXT,
  fingerprint_sha256 TEXT,
  created_at_utc TEXT,
  rotated_at_utc TEXT,
  metadata JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, credential_profile_id, secret_ref_key, resolver_kind),
  FOREIGN KEY (branch_id, projection_hash, credential_profile_id) REFERENCES credential_profile(branch_id, projection_hash, id)
);
