-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_config_api_endpoint (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  capability_name TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL UNIQUE,
  api_endpoint_id TEXT NOT NULL UNIQUE,
  -- RELATIONSHIPS
  skill_config_api_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, capability_name, name, api_endpoint_id),
  FOREIGN KEY (branch_id, projection_hash, skill_config_api_id) REFERENCES skill_config_api(branch_id, projection_hash, id)
);
