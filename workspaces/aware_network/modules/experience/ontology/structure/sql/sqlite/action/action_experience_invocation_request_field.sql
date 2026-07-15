-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action_experience_invocation_request_field (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  action_experience_invocation_id TEXT NOT NULL,
  attribute_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  source_ref TEXT NOT NULL,
  required INTEGER NOT NULL,
  position INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, action_experience_invocation_id, attribute_config_id),
  FOREIGN KEY (branch_id, projection_hash, action_experience_invocation_id) REFERENCES action_experience_invocation(branch_id, projection_hash, id)
);
