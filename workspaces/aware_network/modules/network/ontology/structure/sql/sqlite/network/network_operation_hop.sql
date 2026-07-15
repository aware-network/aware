-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_operation_hop (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  network_operation_id TEXT NOT NULL,
  source_environment_id TEXT,
  source_node_id TEXT,
  target_environment_id TEXT,
  target_node_id TEXT,
  -- ATTRIBUTES
  source_interface_id TEXT,
  target_interface_id TEXT,
  hop_index INTEGER NOT NULL,
  source_app_type TEXT NOT NULL,
  target_app_type TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, network_operation_id, hop_index)
);
