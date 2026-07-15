-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE session_provider (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- ATTRIBUTES
  provider_key TEXT NOT NULL,
  provider_kind TEXT NOT NULL,
  title TEXT,
  status TEXT NOT NULL,
  contract_ref TEXT,
  metadata_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, provider_key)
);
