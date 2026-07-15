-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_config_target (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  name TEXT NOT NULL UNIQUE,
  projection_experience_graph_identity_id TEXT NOT NULL UNIQUE,
  -- RELATIONSHIPS
  skill_config_experience_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, name, projection_experience_graph_identity_id),
  FOREIGN KEY (branch_id, projection_hash, skill_config_experience_id) REFERENCES skill_config_experience(branch_id, projection_hash, id)
);
