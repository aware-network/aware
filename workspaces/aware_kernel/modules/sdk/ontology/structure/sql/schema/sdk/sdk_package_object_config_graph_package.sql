-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sdk_package_object_config_graph_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  sdk_package_id UUID NOT NULL,
  object_config_graph_package_id UUID NOT NULL,
  object_config_graph_package_object_instance_graph_commit_id UUID,
  -- ATTRIBUTES
  role TEXT NOT NULL,
  manifest_relative_path TEXT NOT NULL,
  package_kind TEXT NOT NULL,
  expected_hash_sha256 TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, sdk_package_id, object_config_graph_package_id),
  FOREIGN KEY (branch_id, projection_hash, sdk_package_id) REFERENCES sdk_package(branch_id, projection_hash, id)
);
