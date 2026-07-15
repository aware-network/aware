-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE node_package_included_node_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  included_package_name TEXT NOT NULL,
  -- RELATIONSHIPS
  node_package_id UUID NOT NULL,
  included_node_package_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  include_key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, included_package_name),
  FOREIGN KEY (branch_id, projection_hash, node_package_id) REFERENCES node_package(branch_id, projection_hash, id)
);
