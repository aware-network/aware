-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actuator (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  actuator_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  actuator_instance_key TEXT NOT NULL,
  external_ref TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actuator_config_id, actuator_instance_key)
);
