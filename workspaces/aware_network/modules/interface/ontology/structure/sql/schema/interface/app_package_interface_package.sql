-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE app_package_interface_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  app_package_id UUID NOT NULL,
  interface_package_id UUID NOT NULL,
  interface_package_object_instance_graph_commit_id UUID,
  -- ATTRIBUTES
  description TEXT,
  role TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, app_package_id, interface_package_id),
  FOREIGN KEY (branch_id, projection_hash, app_package_id) REFERENCES app_package(branch_id, projection_hash, id)
);
