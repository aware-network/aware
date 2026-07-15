-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE app_package_interface_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  app_package_id TEXT NOT NULL,
  interface_package_id TEXT NOT NULL,
  interface_package_object_instance_graph_commit_id TEXT,
  -- ATTRIBUTES
  description TEXT,
  role TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, app_package_id, interface_package_id),
  FOREIGN KEY (branch_id, projection_hash, app_package_id) REFERENCES app_package(branch_id, projection_hash, id)
);
