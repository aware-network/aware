-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sensor (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  sensor_instance_key TEXT NOT NULL,
  -- RELATIONSHIPS
  sensor_config_id UUID NOT NULL,
  -- ATTRIBUTES
  external_ref TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, sensor_instance_key)
);
