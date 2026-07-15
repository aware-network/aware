-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE role_config_invocation_action_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  policy_key TEXT NOT NULL,
  role_config_id TEXT NOT NULL,
  -- RELATIONSHIPS
  experience_invocation_action_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  requirement_kind TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, policy_key, role_config_id),
  FOREIGN KEY (branch_id, projection_hash, experience_invocation_action_config_id) REFERENCES experience_invocation_action_config(branch_id, projection_hash, id)
);
