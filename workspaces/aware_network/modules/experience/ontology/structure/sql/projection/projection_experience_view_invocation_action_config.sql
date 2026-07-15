-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_view_invocation_action_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  experience_invocation_action_config_id UUID NOT NULL,
  -- RELATIONSHIPS
  projection_experience_view_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, experience_invocation_action_config_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_view_id) REFERENCES projection_experience_view(branch_id, projection_hash, id)
);
