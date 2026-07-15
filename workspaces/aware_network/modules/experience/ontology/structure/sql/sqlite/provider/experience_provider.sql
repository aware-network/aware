-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_provider (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  metadata_json TEXT,
  provider_key TEXT NOT NULL,
  provider_kind TEXT NOT NULL,
  selection_policy TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, projection_experience_id, provider_key)
);
