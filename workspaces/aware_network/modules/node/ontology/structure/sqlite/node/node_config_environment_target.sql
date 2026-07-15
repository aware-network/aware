-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE node_config_environment_target (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  environment_handle TEXT NOT NULL,
  -- RELATIONSHIPS
  node_config_id TEXT NOT NULL,
  environment_config_id TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, environment_handle),
  FOREIGN KEY (branch_id, projection_hash, node_config_id) REFERENCES node_config(branch_id, projection_hash, id)
);
