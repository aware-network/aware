-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_branch (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_id TEXT NOT NULL,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, projection_experience_id, name),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_id) REFERENCES projection_experience(branch_id, projection_hash, id)
);
