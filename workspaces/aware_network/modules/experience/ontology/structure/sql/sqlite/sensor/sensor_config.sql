-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sensor_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  connector_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  sensor_key TEXT NOT NULL,
  sensor_kind TEXT NOT NULL,
  source_ref TEXT,
  label TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, connector_config_id, sensor_key)
);
