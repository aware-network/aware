-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sensor_invocation_action (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  sensor_invocation_action_config_id UUID NOT NULL,
  experience_invocation_action_id UUID NOT NULL,
  -- RELATIONSHIPS
  sensor_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, sensor_invocation_action_config_id, experience_invocation_action_id)
);
