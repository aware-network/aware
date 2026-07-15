-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_experience_profile_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_experience_id UUID NOT NULL,
  environment_profile_config_id UUID NOT NULL,
  environment_provider_grant_id UUID,
  image_id UUID UNIQUE,
  -- ATTRIBUTES
  description TEXT,
  narrative TEXT,
  key TEXT NOT NULL,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_experience_id, key, environment_profile_config_id)
);
