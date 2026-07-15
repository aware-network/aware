-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_package_object_config_graph_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_package_id TEXT NOT NULL,
  object_config_graph_package_id TEXT NOT NULL,
  object_config_graph_package_object_instance_graph_commit_id TEXT,
  -- ATTRIBUTES
  role TEXT NOT NULL,
  manifest_relative_path TEXT NOT NULL,
  package_kind TEXT NOT NULL,
  expected_hash_sha256 TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_package_id, object_config_graph_package_id),
  FOREIGN KEY (branch_id, projection_hash, service_package_id) REFERENCES service_package(branch_id, projection_hash, id)
);
