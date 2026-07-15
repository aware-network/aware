-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_profile_package_dependency (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_profile_package_id TEXT NOT NULL,
  target_environment_profile_package_id TEXT NOT NULL,
  target_environment_profile_package_object_instance_graph_commit_id TEXT,
  -- ATTRIBUTES
  description TEXT,
  expected_hash_sha256 TEXT,
  target_package_name TEXT NOT NULL,
  target_version_number INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_profile_package_id, target_environment_profile_package_id),
  FOREIGN KEY (branch_id, projection_hash, environment_profile_package_id) REFERENCES environment_profile_package(branch_id, projection_hash, id)
);
