-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sdk_package_dependency (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  sdk_package_id UUID NOT NULL,
  target_sdk_package_id UUID NOT NULL,
  target_sdk_package_object_instance_graph_commit_id UUID,
  -- ATTRIBUTES
  target_package_name TEXT NOT NULL,
  target_version_number INTEGER,
  expected_hash_sha256 TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, sdk_package_id, target_sdk_package_id),
  FOREIGN KEY (branch_id, projection_hash, sdk_package_id) REFERENCES sdk_package(branch_id, projection_hash, id)
);
