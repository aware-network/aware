-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE node_config_interface_target (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  node_config_id TEXT NOT NULL,
  interface_config_id TEXT,
  -- ATTRIBUTES
  interface_name TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, node_config_id, interface_name),
  FOREIGN KEY (branch_id, projection_hash, node_config_id) REFERENCES node_config(branch_id, projection_hash, id)
);
