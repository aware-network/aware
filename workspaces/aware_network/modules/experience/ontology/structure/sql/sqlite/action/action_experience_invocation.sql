-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action_experience_invocation (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  action_experience_id TEXT NOT NULL,
  experience_invocation_action_config_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, action_experience_id, experience_invocation_action_config_id),
  FOREIGN KEY (branch_id, projection_hash, action_experience_id) REFERENCES action_experience(branch_id, projection_hash, id)
);
