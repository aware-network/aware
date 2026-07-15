-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_config_experience (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  skill_config_id TEXT NOT NULL,
  projection_experience_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, skill_config_id, projection_experience_id),
  FOREIGN KEY (branch_id, projection_hash, skill_config_id) REFERENCES skill_config(branch_id, projection_hash, id)
);
