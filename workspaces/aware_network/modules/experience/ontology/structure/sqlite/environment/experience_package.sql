-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  name TEXT NOT NULL,
  -- RELATIONSHIPS
  source_code_package_id TEXT,
  environment_experience_id TEXT NOT NULL UNIQUE,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, name)
);
