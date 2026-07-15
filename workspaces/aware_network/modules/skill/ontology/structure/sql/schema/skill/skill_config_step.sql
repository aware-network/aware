-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_config_step (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  skill_config_id UUID NOT NULL,
  skill_config_api_endpoint_id UUID NOT NULL,
  -- ATTRIBUTES
  instruction TEXT NOT NULL,
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, skill_config_id, position),
  FOREIGN KEY (branch_id, projection_hash, skill_config_id) REFERENCES skill_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, skill_config_api_endpoint_id) REFERENCES skill_config_api_endpoint(branch_id, projection_hash, id)
);
