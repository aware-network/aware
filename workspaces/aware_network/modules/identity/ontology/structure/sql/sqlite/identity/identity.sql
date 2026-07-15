-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE identity (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  human_id TEXT UNIQUE,
  organization_id TEXT UNIQUE,
  identity_profile_id TEXT UNIQUE,
  -- ATTRIBUTES
  public_key TEXT NOT NULL,
  type_ TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, public_key, type_),
  FOREIGN KEY (branch_id, projection_hash, human_id) REFERENCES human(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, identity_profile_id) REFERENCES identity_profile(branch_id, projection_hash, id)
);
