-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action_experience_program (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  program_config_id UUID NOT NULL,
  -- RELATIONSHIPS
  action_experience_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, program_config_id),
  FOREIGN KEY (branch_id, projection_hash, action_experience_id) REFERENCES action_experience(branch_id, projection_hash, id)
);
