-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE node_config_service_target (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  service_name TEXT NOT NULL,
  -- RELATIONSHIPS
  node_config_id TEXT NOT NULL,
  service_config_id TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, service_name),
  FOREIGN KEY (branch_id, projection_hash, node_config_id) REFERENCES node_config(branch_id, projection_hash, id)
);
