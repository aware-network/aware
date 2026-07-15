-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_config_api_endpoint (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  skill_config_api_id TEXT NOT NULL,
  api_endpoint_id TEXT NOT NULL,
  -- ATTRIBUTES
  capability_name TEXT NOT NULL,
  description TEXT,
  name TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, skill_config_api_id, capability_name, name, api_endpoint_id),
  FOREIGN KEY (branch_id, projection_hash, skill_config_api_id) REFERENCES skill_config_api(branch_id, projection_hash, id)
);
