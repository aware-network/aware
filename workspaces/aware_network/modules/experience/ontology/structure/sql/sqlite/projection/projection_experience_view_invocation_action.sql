-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_view_invocation_action (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_view_instance_id TEXT NOT NULL,
  view_invocation_action_config_id TEXT NOT NULL,
  experience_invocation_action_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, projection_experience_view_instance_id, view_invocation_action_config_id, experience_invocation_action_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_view_instance_id) REFERENCES projection_experience_view_instance(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, view_invocation_action_config_id) REFERENCES projection_experience_view_invocation_action_config(branch_id, projection_hash, id)
);
