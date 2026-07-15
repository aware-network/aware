-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sensor_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  sensor_key TEXT NOT NULL,
  -- RELATIONSHIPS
  connector_config_id UUID NOT NULL,
  -- ATTRIBUTES
  sensor_kind TEXT NOT NULL,
  source_ref TEXT,
  label TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, sensor_key)
);
