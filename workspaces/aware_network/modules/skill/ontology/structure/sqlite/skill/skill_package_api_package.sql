-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_package_api_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  api_package_id TEXT NOT NULL UNIQUE,
  -- RELATIONSHIPS
  skill_package_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, api_package_id),
  FOREIGN KEY (branch_id, projection_hash, skill_package_id) REFERENCES skill_package(branch_id, projection_hash, id)
);
