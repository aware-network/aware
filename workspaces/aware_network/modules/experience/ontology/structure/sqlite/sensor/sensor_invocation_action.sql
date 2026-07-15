-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sensor_invocation_action (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  sensor_invocation_action_config_id TEXT NOT NULL,
  experience_invocation_action_id TEXT NOT NULL,
  -- RELATIONSHIPS
  sensor_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, sensor_invocation_action_config_id, experience_invocation_action_id)
);
