-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_config_step (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  position INTEGER NOT NULL UNIQUE,
  -- RELATIONSHIPS
  skill_config_id TEXT NOT NULL,
  skill_config_api_endpoint_id TEXT NOT NULL,
  -- ATTRIBUTES
  instruction TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, position),
  FOREIGN KEY (branch_id, projection_hash, skill_config_id) REFERENCES skill_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, skill_config_api_endpoint_id) REFERENCES skill_config_api_endpoint(branch_id, projection_hash, id)
);
