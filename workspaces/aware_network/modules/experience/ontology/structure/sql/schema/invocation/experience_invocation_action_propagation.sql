-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_invocation_action_propagation (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  experience_invocation_action_id UUID NOT NULL,
  target_invocation_action_id UUID NOT NULL,
  -- ATTRIBUTES
  propagation_kind TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, experience_invocation_action_id, target_invocation_action_id),
  FOREIGN KEY (branch_id, projection_hash, experience_invocation_action_id) REFERENCES experience_invocation_action(branch_id, projection_hash, id)
);
