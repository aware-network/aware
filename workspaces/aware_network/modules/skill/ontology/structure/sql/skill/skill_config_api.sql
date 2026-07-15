-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_config_api (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  api_id UUID NOT NULL UNIQUE,
  -- RELATIONSHIPS
  skill_config_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, api_id),
  FOREIGN KEY (branch_id, projection_hash, skill_config_id) REFERENCES skill_config(branch_id, projection_hash, id)
);
