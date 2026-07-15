-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_package_provided_api_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_package_id TEXT NOT NULL,
  api_package_id TEXT NOT NULL,
  api_package_object_instance_graph_commit_id TEXT NOT NULL,
  service_protocol_package_id TEXT NOT NULL,
  -- ATTRIBUTES
  service_protocol_plan_hash_sha256 TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_package_id, api_package_id),
  FOREIGN KEY (branch_id, projection_hash, service_package_id) REFERENCES service_package(branch_id, projection_hash, id)
);
