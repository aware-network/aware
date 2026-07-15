-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action_experience_invocation_request_field (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  action_experience_invocation_id UUID NOT NULL,
  attribute_config_id UUID NOT NULL,
  -- ATTRIBUTES
  source_ref TEXT NOT NULL,
  required BOOLEAN NOT NULL,
  position INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, action_experience_invocation_id, attribute_config_id),
  FOREIGN KEY (branch_id, projection_hash, action_experience_invocation_id) REFERENCES action_experience_invocation(branch_id, projection_hash, id)
);
