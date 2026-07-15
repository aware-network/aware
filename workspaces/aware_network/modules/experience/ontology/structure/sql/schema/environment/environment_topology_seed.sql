-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_topology_seed (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_experience_id UUID NOT NULL,
  environment_experience_profile_config_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  key TEXT NOT NULL,
  narrative TEXT,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_experience_id, key, environment_experience_profile_config_id)
);
