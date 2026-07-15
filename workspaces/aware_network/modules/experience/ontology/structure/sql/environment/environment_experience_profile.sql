-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_experience_profile (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  profile_config_id UUID NOT NULL,
  environment_profile_id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_experience_id UUID NOT NULL,
  -- ATTRIBUTES
  title TEXT,
  status TEXT NOT NULL,
  description TEXT,
  metadata_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, profile_config_id, environment_profile_id)
);
