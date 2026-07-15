-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE connector_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  connector_key TEXT NOT NULL,
  -- ATTRIBUTES
  connector_kind TEXT NOT NULL,
  label TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, connector_key)
);
