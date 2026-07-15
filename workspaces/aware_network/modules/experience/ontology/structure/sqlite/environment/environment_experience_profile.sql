-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_experience_profile (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  profile_config_id TEXT NOT NULL,
  environment_profile_id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_experience_id TEXT NOT NULL,
  -- ATTRIBUTES
  title TEXT,
  status TEXT NOT NULL,
  description TEXT,
  metadata_json TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, profile_config_id, environment_profile_id)
);
