-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actuator_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  connector_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  actuator_key TEXT NOT NULL,
  actuator_kind TEXT NOT NULL,
  target_ref TEXT,
  label TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, connector_config_id, actuator_key)
);
