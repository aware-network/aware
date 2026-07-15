-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_provider (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  provider_key TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  metadata_json JSONB,
  provider_kind TEXT NOT NULL,
  selection_policy TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, provider_key)
);
