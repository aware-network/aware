-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_experience_program (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  program_config_id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_experience_thread_config_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, program_config_id),
  FOREIGN KEY (branch_id, projection_hash, environment_experience_thread_config_id) REFERENCES environment_experience_thread_config(branch_id, projection_hash, id)
);
