-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE connector_provider (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  provider_key TEXT NOT NULL,
  -- RELATIONSHIPS
  connector_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  provider_kind TEXT NOT NULL,
  provider_ref TEXT,
  label TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, provider_key)
);
