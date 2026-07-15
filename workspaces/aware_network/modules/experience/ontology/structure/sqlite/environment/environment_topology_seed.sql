-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_topology_seed (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  key TEXT NOT NULL,
  environment_experience_profile_config_id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_experience_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  narrative TEXT,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, key, environment_experience_profile_config_id)
);
