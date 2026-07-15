-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_experience_event (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_experience_profile_config_id UUID NOT NULL,
  event_config_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_experience_profile_config_id, event_config_id),
  FOREIGN KEY (branch_id, projection_hash, environment_experience_profile_config_id) REFERENCES environment_experience_profile_config(branch_id, projection_hash, id)
);
