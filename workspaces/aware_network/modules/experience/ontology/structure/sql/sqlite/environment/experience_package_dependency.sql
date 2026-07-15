-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_package_dependency (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  experience_package_id TEXT NOT NULL,
  target_experience_package_id TEXT NOT NULL,
  target_experience_package_object_instance_graph_commit_id TEXT,
  -- ATTRIBUTES
  target_package_name TEXT NOT NULL,
  target_version_number INTEGER,
  expected_hash_sha256 TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, experience_package_id, target_experience_package_id),
  FOREIGN KEY (branch_id, projection_hash, experience_package_id) REFERENCES experience_package(branch_id, projection_hash, id)
);
