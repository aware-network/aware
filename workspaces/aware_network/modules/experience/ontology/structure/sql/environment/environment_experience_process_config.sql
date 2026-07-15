-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_experience_process_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  key TEXT NOT NULL,
  process_config_id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_experience_profile_config_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  intent TEXT,
  narrative TEXT,
  position INTEGER,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, key, process_config_id),
  FOREIGN KEY (branch_id, projection_hash, environment_experience_profile_config_id) REFERENCES environment_experience_profile_config(branch_id, projection_hash, id)
);
